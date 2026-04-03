package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"groundbit-visual-api/internal/config"
)

type WhatsAppService struct {
	cfg    *config.Config
	client *http.Client
}

func NewWhatsAppService(cfg *config.Config) *WhatsAppService {
	return &WhatsAppService{cfg: cfg, client: &http.Client{}}
}

func (s *WhatsAppService) DownloadMedia(mediaID string) ([]byte, string, error) {
	// Step 1: get media URL and mime type
	metaURL := fmt.Sprintf("https://graph.facebook.com/v19.0/%s", mediaID)
	req, _ := http.NewRequest("GET", metaURL, nil)
	req.Header.Set("Authorization", "Bearer "+s.cfg.WhatsAppToken)

	resp, err := s.client.Do(req)
	if err != nil {
		return nil, "", fmt.Errorf("media meta fetch failed: %w", err)
	}
	defer resp.Body.Close()

	var meta map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&meta)

	mediaURL, _ := meta["url"].(string)
	mimeType, _ := meta["mime_type"].(string)
	if mimeType == "" {
		mimeType = "image/jpeg"
	}

	// Step 2: download actual bytes
	req2, _ := http.NewRequest("GET", mediaURL, nil)
	req2.Header.Set("Authorization", "Bearer "+s.cfg.WhatsAppToken)

	resp2, err := s.client.Do(req2)
	if err != nil {
		return nil, "", fmt.Errorf("media download failed: %w", err)
	}
	defer resp2.Body.Close()

	imageBytes, err := io.ReadAll(resp2.Body)
	return imageBytes, mimeType, err
}

func (s *WhatsAppService) SendMessage(to, message string) error {
	url := fmt.Sprintf(
		"https://graph.facebook.com/v19.0/%s/messages",
		s.cfg.WhatsAppPhoneID,
	)

	body := map[string]interface{}{
		"messaging_product": "whatsapp",
		"to":                to,
		"type":              "text",
		"text":              map[string]string{"body": message},
	}

	jsonBody, _ := json.Marshal(body)
	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(jsonBody))
	req.Header.Set("Authorization", "Bearer "+s.cfg.WhatsAppToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("send message failed: %w", err)
	}
	defer resp.Body.Close()
	return nil
}
