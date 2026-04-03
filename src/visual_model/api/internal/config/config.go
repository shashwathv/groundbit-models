package config

import "os"

type Config struct {
	Port               string
	GeminiAPIKey       string
	WhatsAppToken      string
	WhatsAppPhoneID    string
	WebhookVerifyToken string
	AWSAccessKey       string
	AWSSecretKey       string
	AWSBucketName      string
	AWSRegion          string
}

func Load() *Config {
	return &Config{
		Port:               getEnv("PORT", "8080"),
		GeminiAPIKey:       getEnv("GEMINI_API_KEY", ""),
		WhatsAppToken:      getEnv("WHATSAPP_TOKEN", ""),
		WhatsAppPhoneID:    getEnv("WHATSAPP_PHONE_ID", ""),
		WebhookVerifyToken: getEnv("WEBHOOK_VERIFY_TOKEN", ""),
		AWSAccessKey:       getEnv("AWS_ACCESS_KEY", ""),
		AWSSecretKey:       getEnv("AWS_SECRET_KEY", ""),
		AWSBucketName:      getEnv("AWS_BUCKET_NAME", "agri-file-upload"),
		AWSRegion:          getEnv("AWS_REGION", "eu-north-1"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
