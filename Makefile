build:
	gcloud --project=api-project-922752677763 builds submit --tag gcr.io/api-project-922752677763/book-search-api:latest

deploy:
	gcloud run deploy book-search-api \
				 --project=api-project-922752677763 \
				 --image gcr.io/api-project-922752677763/book-search-api:latest \
				 --platform managed \
				 --memory=4Gi \
				 --cpu=2 \
				 --concurrency=100 \
				 --min-instances=0 \
				 --max-instances=100 \
				 --timeout=1200 \
				 --region=us-east4 \