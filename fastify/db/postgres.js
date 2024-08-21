
require('dotenv').config();
const db_name = process.env.PGDB || "benchmark_db";
const db_user = process.env.PGUSER || "postgres";
const db_pass = process.env.PGPASS || "root";
const db_host = process.env.PGHOST || "localhost";

const knex = require("knex")({
  client: "pg",
  connection: {
    host: db_host,
    user: db_user,
    password: db_pass,
    database: db_name,
    ssl: {
      require: true,
      rejectUnauthorized: false
    }
  }
});

async function allFortunes() {
  return knex("Fortune").select("*");
}

async function getWorld(id) {
  return knex("World")
    .first()
    .where({ id });
}

async function saveWorlds(worlds) {
  const updates = [];

  worlds.forEach(world => {
    const { id, randomNumber } = world;

    updates.push(
      knex("World")
        .update({ randomnumber: randomNumber })
        .where({ id })
    );
  });

  return Promise.all(updates);
}

module.exports = {
  getWorld,
  saveWorlds,
  allFortunes
};
