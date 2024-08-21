/**
 * Module dependencies.
 */
const cluster = require('cluster');
const numCPUs = require('os').cpus().length;
const express = require('express');
const helper = require('./helper');
require('dotenv').config();

// Middleware
const bodyParser = require('body-parser');

const { Sequelize } = require('sequelize');

const db_name = process.env.PGDB || "benchmark_db";
const db_user = process.env.PGUSER || "postgres";
const db_pass = process.env.PGPASS || "root";
const db_host = process.env.PGHOST || "localhost";

const sequelize = new Sequelize(db_name, db_user, db_pass, {
  host: db_host,
  dialect: 'postgres',
  logging: false,
  pool: {
    max: 50,
    min: 0,
    idle: 10000
  },
  dialectOptions: {
    ssl: {
      require: true,
      rejectUnauthorized: false
    }
  }
});

const Worlds = sequelize.define('world', {
  id: {
    type: Sequelize.INTEGER,
    primaryKey: true
  },
  randomnumber: { type: Sequelize.INTEGER }
}, {
  timestamps: false,
  freezeTableName: true
});

const Fortunes = sequelize.define('fortune', {
  id: {
    type: Sequelize.INTEGER,
    primaryKey: true
  },
  message: { type: Sequelize.STRING }
}, {
  timestamps: false,
  freezeTableName: true
});

const randomWorldPromise = () => {
  return Worlds.findOne({
    where: { id: helper.randomizeNum() }
  }).then((result) => {
    return result;
  }).catch((err) => process.exit(1));
};

if (cluster.isPrimary) {
  // Fork workers.
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code, signal) =>
    console.log('worker ' + worker.process.pid + ' died'));
} else {
  const app = express();

  app.use(bodyParser.urlencoded({ extended: true }));

  // Set headers for all routes
  app.use((req, res, next) => {
    res.setHeader("Server", "Express");
    return next();
  });

  app.set('view engine', 'pug');
  app.set('views', __dirname + '/views');

  // Routes
  app.get('/db', async (req, res) => {
    let world = await randomWorldPromise();

    res.setHeader("Content-Type", "application/json");
    res.json(world);
  });

  app.get('/json', (req, res) => res.send({ message: 'Hello, World!' }));

  app.get('/plaintext', (req, res) =>
    res.header('Content-Type', 'text/plain').send('Hello, World!'));
  
  app.get('/dbs', async (req, res) => {
    const queries = Math.min(parseInt(req.query.queries) || 1, 500);

    const promisesArray = [];

    for (let i = 0; i < queries; i++) {
      promisesArray.push(randomWorldPromise());
    }

    res.json(await Promise.all(promisesArray));
  });

  app.get('/fortunes', async (req, res) => {
    let fortunes = await Fortunes.findAll();
    const newFortune = { id: 0, message: "Additional fortune added at request time." };
    fortunes.push(newFortune);
    fortunes.sort((a, b) => (a.message < b.message) ? -1 : 1);

    res.render('fortunes/index', { fortunes: fortunes });
  });

  app.get('/updates', async (req, res) => {
    const queries = Math.min(parseInt(req.query.queries) || 1, 500);
    const worldPromises = [];

    for (let i = 0; i < queries; i++) {
      worldPromises.push(randomWorldPromise());
    }

    const worldUpdate = (world) => {
      world.randomnumber = helper.randomizeNum();

      return Worlds.update({
            randomnumber: world.randomnumber
          },
          {
            where: { id: world.id }
          }).then(() => {
        return world;
      }).catch((err) => process.exit(1));
    };

    Promise.all(worldPromises).then((worlds) => {
      const updates = worlds.map((e) => worldUpdate(e));

      Promise.all(updates).then((updated) => {
        res.json(updated);
      });
    });
  });

  app.listen(8080, () => {
    console.log('listening on port 8080');
  });
}
