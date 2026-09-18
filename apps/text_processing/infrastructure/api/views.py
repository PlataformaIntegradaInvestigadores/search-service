import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ...application.services.text_vectorizer_service import TextVectorizerService

logger = logging.getLogger(__name__)


class TextVectorizeView(APIView):
    """
    API endpoint to vectorize text input
    """

    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.vectorizer_service = TextVectorizerService()

    def post(self, request):
        """
        Vectorize input text

        Expected payload:
        {
            "text": "Your text here...",
            "translate_to_english": true,  // optional, default true
            "clean_text": true            // optional, default true
        }
        """
        try:
            # Get input data
            text = request.data.get("text")
            translate_to_english = request.data.get("translate_to_english", True)
            clean_text = request.data.get("clean_text", True)

            # Validate input
            if not text:
                return Response(
                    {"error": "Text field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not isinstance(text, str) or len(text.strip()) == 0:
                return Response(
                    {"error": "Text must be a non-empty string"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process text
            result = self.vectorizer_service.vectorize_text(
                text=text,
                translate_to_english=translate_to_english,
                clean_text=clean_text,
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in text vectorization endpoint: {str(e)}")
            return Response(
                {"error": "Internal server error during text processing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TextProcessingHealthView(APIView):
    """
    Health check endpoint for text processing service
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Check if text processing service is healthy"""
        try:
            vectorizer_service = TextVectorizerService()

            # Test with a simple text
            test_result = vectorizer_service.vectorize_text(
                text="test", translate_to_english=False, clean_text=False
            )

            return Response(
                {
                    "status": "healthy",
                    "service": "text_processing",
                    "model_dimension": test_result["dimension"],
                    "message": "Text processing service is operational",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response(
                {"status": "unhealthy", "service": "text_processing", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
