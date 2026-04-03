package service

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"time"

	"groundbit-visual-api/internal/config"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type S3Service struct {
	client *s3.Client
	bucket string
}

func NewS3Service(cfg *config.Config) *S3Service {
	awsCfg, _ := awsconfig.LoadDefaultConfig(
		context.TODO(),
		awsconfig.WithRegion(cfg.AWSRegion),
		awsconfig.WithCredentialsProvider(
			credentials.NewStaticCredentialsProvider(
				cfg.AWSAccessKey,
				cfg.AWSSecretKey,
				"",
			),
		),
	)

	return &S3Service{
		client: s3.NewFromConfig(awsCfg),
		bucket: cfg.AWSBucketName,
	}
}

func (s *S3Service) Upload(data []byte, from, mimeType string) (string, error) {
	key := fmt.Sprintf("uploads/%s_%d.jpg", from, time.Now().UnixMilli())

	_, err := s.client.PutObject(context.TODO(), &s3.PutObjectInput{
		Bucket:      aws.String(s.bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(data),
		ContentType: aws.String(mimeType),
	})
	return key, err
}

func (s *S3Service) Fetch(key string) ([]byte, error) {
	out, err := s.client.GetObject(context.TODO(), &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("S3 fetch failed: %w", err)
	}
	defer out.Body.Close()
	return io.ReadAll(out.Body)
}
