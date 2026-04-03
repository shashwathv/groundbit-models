package handler

import (
	"fmt"
	"io"
	"log"
	"net/http"

	"groundbit-visual-api/internal/config"
	"groundbit-visual-api/internal/model"
	"groundbit-visual-api/internal/service"

	"github.com/gin-gonic/gin"
)

type WebhookHandler struct {
	cfg       *config.Config
	s3Svc     *service.S3Service
	geminiSvc *service.GeminiService
	waSvc     *service.WhatsAppService
}

func NewWebhookHandler(
	cfg *config.Config,
	s3 *service.S3Service,
	gemini *service.GeminiService,
	wa *service.WhatsAppService,
) *WebhookHandler {
	return &WebhookHandler{
		cfg:       cfg,
		s3Svc:     s3,
		geminiSvc: gemini,
		waSvc:     wa,
	}
}

func Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

// Verify handles WhatsApp webhook verification handshake
func (h *WebhookHandler) Verify(c *gin.Context) {
	mode := c.Query("hub.mode")
	token := c.Query("hub.verify_token")
	challenge := c.Query("hub.challenge")

	if mode == "subscribe" && token == h.cfg.WebhookVerifyToken {
		c.String(http.StatusOK, challenge)
		return
	}

	c.JSON(http.StatusForbidden, gin.H{"error": "verification failed"})
}

// Receive handles incoming WhatsApp messages
func (h *WebhookHandler) Receive(c *gin.Context) {
	var payload map[string]interface{}
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload"})
		return
	}

	msg, err := extractMessage(payload)
	if err != nil {
		log.Printf("Skipping non-image message: %v", err)
		c.Status(http.StatusOK)
		return
	}

	log.Printf("Image received from %s, media_id: %s", msg.From, msg.MediaID)

	// Acknowledge WhatsApp immediately
	c.Status(http.StatusOK)

	// Process pipeline in background
	go h.process(msg)
}

func (h *WebhookHandler) process(msg *model.WhatsAppMessage) {
	// Step 1: Download image from WhatsApp
	imageBytes, mimeType, err := h.waSvc.DownloadMedia(msg.MediaID)
	if err != nil {
		log.Printf("Download failed: %v", err)
		h.waSvc.SendMessage(msg.From, "Sorry, we could not download your image. Please try again.")
		return
	}

	// Step 2: Upload to S3
	s3Key, err := h.s3Svc.Upload(imageBytes, msg.From, mimeType)
	if err != nil {
		log.Printf("S3 upload failed: %v", err)
		h.waSvc.SendMessage(msg.From, "Sorry, there was a storage error. Please try again.")
		return
	}
	log.Printf("Uploaded to S3: %s", s3Key)

	// Step 3: Fetch back from S3
	fetchedBytes, err := h.s3Svc.Fetch(s3Key)
	if err != nil {
		log.Printf("S3 fetch failed: %v", err)
		h.waSvc.SendMessage(msg.From, "Sorry, there was a retrieval error. Please try again.")
		return
	}

	// Step 4: Analyze with Gemini
	result, err := h.geminiSvc.Analyze(fetchedBytes, mimeType)
	if err != nil {
		log.Printf("Gemini failed: %v", err)
		h.waSvc.SendMessage(msg.From, "Sorry, we could not analyze your image. Please send a clearer photo of the leaf.")
		return
	}

	// Step 5: Reply to farmer
	reply := formatReply(result)
	h.waSvc.SendMessage(msg.From, reply)
	log.Printf("Reply sent to %s", msg.From)
}

func formatReply(r *model.GeminiResult) string {
	if !r.IsLeaf {
		return "We could not detect a crop leaf in your image. Please send a clear photo of the affected leaf."
	}
	return fmt.Sprintf(
		"🌿 *GroundBit Crop Analysis*\n\n"+
			"🪴 *Crop:* %s\n"+
			"🦠 *Disease:* %s\n"+
			"⚠️ *Severity:* %s\n\n"+
			"💊 *Treatment:*\n%s",
		r.Crop, r.Disease, r.Severity, r.Treatment,
	)
}

func extractMessage(payload map[string]interface{}) (*model.WhatsAppMessage, error) {
	entry, ok := payload["entry"].([]interface{})
	if !ok || len(entry) == 0 {
		return nil, fmt.Errorf("no entry")
	}
	changes, ok := entry[0].(map[string]interface{})["changes"].([]interface{})
	if !ok || len(changes) == 0 {
		return nil, fmt.Errorf("no changes")
	}
	value, ok := changes[0].(map[string]interface{})["value"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("no value")
	}
	messages, ok := value["messages"].([]interface{})
	if !ok || len(messages) == 0 {
		return nil, fmt.Errorf("no messages")
	}
	message, ok := messages[0].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("bad message format")
	}

	msgType, _ := message["type"].(string)
	if msgType != "image" {
		return nil, fmt.Errorf("not an image, got: %s", msgType)
	}

	from, _ := message["from"].(string)
	image, ok := message["image"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("no image field")
	}
	mediaID, _ := image["id"].(string)

	return &model.WhatsAppMessage{
		From:    from,
		MediaID: mediaID,
	}, nil
}

func (h *WebhookHandler) TestAnalyze(c *gin.Context) {
	file, err := c.FormFile("image")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no image provided"})
		return
	}

	src, err := file.Open()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "could not open image"})
		return
	}
	defer src.Close()

	imageBytes, err := io.ReadAll(src)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "could not read image"})
		return
	}

	mimeType := file.Header.Get("Content-Type")
	if mimeType == "" {
		mimeType = "image/jpeg"
	}

	result, err := h.geminiSvc.Analyze(imageBytes, mimeType)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}
