package router

import (
	"groundbit-visual-api/internal/config"
	"groundbit-visual-api/internal/handler"
	"groundbit-visual-api/internal/middleware"
	"groundbit-visual-api/internal/service"

	"github.com/gin-gonic/gin"
)

func New(cfg *config.Config) *gin.Engine {
	r := gin.Default()

	r.Use(middleware.CORS())

	s3Svc := service.NewS3Service(cfg)
	geminiSvc := service.NewGeminiService(cfg)
	waSvc := service.NewWhatsAppService(cfg)

	wh := handler.NewWebhookHandler(cfg, s3Svc, geminiSvc, waSvc)

	r.GET("/health", handler.Health)
	r.GET("/webhook", wh.Verify)
	r.POST("/webhook", wh.Receive)
	r.POST(("/test", wh.Testwh.TestAnalyze))

	return r
}
