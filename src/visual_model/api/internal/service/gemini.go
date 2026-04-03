package service

import (
	"context"
	"fmt"
	"strings"

	"groundbit-visual-api/internal/config"
	"groundbit-visual-api/internal/model"

	"google.golang.org/genai"
)

type GeminiService struct {
	cfg *config.Config
}

func NewGeminiService(cfg *config.Config) *GeminiService {
	return &GeminiService{cfg: cfg}
}

const prompt = `You are an expert agricultural plant pathologist.
Analyze this crop leaf image and respond in exactly this format:

CROP: <crop name>
DISEASE: <disease name or "Healthy">
SEVERITY: <Mild / Moderate / Severe / None>
TREATMENT: <2-3 practical treatment steps for the farmer>

If the image does not contain a crop leaf, respond with:
NOT_A_LEAF

Be concise and practical. Respond only in the format above.`

func (s *GeminiService) Analyze(imageBytes []byte, mimeType string) (*model.GeminiResult, error) {
	ctx := context.Background()

	client, err := genai.NewClient(ctx, &genai.ClientConfig{
		APIKey:  s.cfg.GeminiAPIKey,
		Backend: genai.BackendGeminiAPI,
	})
	if err != nil {
		return nil, fmt.Errorf("gemini client error: %w", err)
	}

	contents := []*genai.Content{
		{
			Parts: []*genai.Part{
				{Text: prompt},
				{
					InlineData: &genai.Blob{
						MIMEType: mimeType,
						Data:     imageBytes,
					},
				},
			},
		},
	}

	resp, err := client.Models.GenerateContent(
		ctx,
		"gemini-2.0-flash",
		contents,
		nil,
	)
	if err != nil {
		return nil, fmt.Errorf("gemini generate error: %w", err)
	}

	if len(resp.Candidates) == 0 {
		return nil, fmt.Errorf("empty gemini response")
	}

	raw := resp.Text()
	return parseGeminiResponse(raw), nil
}

func parseGeminiResponse(raw string) *model.GeminiResult {
	if strings.Contains(strings.ToUpper(raw), "NOT_A_LEAF") {
		return &model.GeminiResult{IsLeaf: false}
	}

	result := &model.GeminiResult{IsLeaf: true}
	lines := strings.Split(raw, "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		switch {
		case strings.HasPrefix(line, "CROP:"):
			result.Crop = strings.TrimSpace(strings.TrimPrefix(line, "CROP:"))
		case strings.HasPrefix(line, "DISEASE:"):
			result.Disease = strings.TrimSpace(strings.TrimPrefix(line, "DISEASE:"))
		case strings.HasPrefix(line, "SEVERITY:"):
			result.Severity = strings.TrimSpace(strings.TrimPrefix(line, "SEVERITY:"))
		case strings.HasPrefix(line, "TREATMENT:"):
			result.Treatment = strings.TrimSpace(strings.TrimPrefix(line, "TREATMENT:"))
		}
	}

	return result
}
