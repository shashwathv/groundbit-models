package main

import (
	"log"

	"groundbit-visual-api/internal/config"
	"groundbit-visual-api/internal/router"

	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file, reading from environment")
	}

	cfg := config.Load()
	r := router.New(cfg)

	log.Printf("GroundBit Visual API running on :%s", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
