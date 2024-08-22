package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// World represents an entry in the World table
type World struct {
	ID           int64 `json:"id"`
	RandomNumber int64 `json:"randomNumber" gorm:"column:randomnumber"`
}

// TableName overrides the table name used by World to `World`
func (World) TableName() string {
	return "World"
}

// getWorld implements the logic behind the query tests
func getWorld(db *gorm.DB) World {
	randomId := rand.Intn(10000) + 1

	var world World
	db.Take(&world, randomId)

	return world
}

// processWorld implements the logic behind the updates tests
func processWorld(tx *gorm.DB) (World, error) {
	randomId := rand.Intn(10000) + 1
	randomId2 := int64(rand.Intn(10000) + 1)

	var world World
	tx.Take(&world, randomId)

	world.RandomNumber = randomId2
	err := tx.Save(&world).Error

	return world, err
}

func main() {
	// Setup DB and Web Server
	dbname := os.Getenv("PGDB")
	if dbname == "" {
		dbname = "benchmark_db"
	}
	dbuser := os.Getenv("PGUSER")
	if dbuser == "" {
		dbuser = "postgres"
	}
	dbpass := os.Getenv("PGPASS")
	if dbpass == "" {
		dbpass = "root"
	}
	dbhost := os.Getenv("PGHOST")
	if dbhost == "" {
		dbhost = "localhost"
	}

	dsn := "host=" + dbhost + " user=" + dbuser + " password=" + dbpass + " dbname=" + dbname + " port=5432 " + "sslmode=require"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		PrepareStmt: true,
		Logger:      logger.Default.LogMode(logger.Silent),
	})

	if err != nil {
		panic("failed to connect database")
	}

	sqlDB, err := db.DB()
	if err != nil {
		panic("failed to get underlying db conn pooling struct")
	}

	// SetMaxIdleConns sets the maximum number of connections in the idle connection pool.
	sqlDB.SetMaxIdleConns(500)

	// Gin setup
	r := gin.New()

	// Setup middleware to add server header
	serverHeader := []string{"Gin-gorm"}
	r.Use(func(c *gin.Context) {
		c.Writer.Header()["Server"] = serverHeader
	})

	// JSON Test
	r.GET("/json", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "Hello, World!"})
	})

	// Plaintext Test
	r.GET("/plaintext", func(c *gin.Context) {
		c.String(200, "Hello, World!")
	})

	// Single Query
	r.GET("/db", func(c *gin.Context) {
		world := getWorld(db)
		c.JSON(200, world)
	})

	type NumOf struct {
		Queries int `form:"queries"`
	}

	// Multiple Queries
	r.GET("/dbs", func(c *gin.Context) {
		var numOf NumOf

		if c.ShouldBindQuery(&numOf) != nil {
			numOf.Queries = 1
		} else if numOf.Queries < 1 {
			numOf.Queries = 1
		} else if numOf.Queries > 500 {
			numOf.Queries = 500
		}

		worlds := make([]World, numOf.Queries)
		channel := make(chan World, numOf.Queries)

		for i := 0; i < numOf.Queries; i++ {
			go func() { channel <- getWorld(db) }()
		}

		for i := 0; i < numOf.Queries; i++ {
			worlds[i] = <-channel
		}

		c.JSON(200, worlds)
	})

	// Multiple Updates
	r.GET("/updates", func(c *gin.Context) {
		var numOf NumOf

		if c.ShouldBindQuery(&numOf) != nil {
			numOf.Queries = 1
		} else if numOf.Queries < 1 {
			numOf.Queries = 1
		} else if numOf.Queries > 500 {
			numOf.Queries = 500
		}

		worlds := make([]World, numOf.Queries)
		var err error

		for i := 0; i < numOf.Queries; i++ {
			worlds[i], err = processWorld(db)
			if err != nil {
				fmt.Println(err)
				c.JSON(500, gin.H{"error": err})
				return
			}
		}

		c.JSON(200, worlds)
	})

	// Start service
	s := &http.Server{
		Addr:         ":8080",
		Handler:      r,
		ReadTimeout:  100000 * time.Second,
		WriteTimeout: 100000 * time.Second,
	}

	s.ListenAndServe()
}
