package model

type GeminiResult struct {
	Crop      string
	Disease   string
	Severity  string
	Treatment string
	IsLeaf    bool
}

type WhatsAppMessage struct {
	From    string
	MediaID string
}
