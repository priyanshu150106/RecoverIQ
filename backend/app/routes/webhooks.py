from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.webhook_processor import webhook_processor, WebhookProcessingError

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
    summary="Razorpay Webhook Receiver",
    description="Receives, verifies, and idempotently processes Razorpay Payment Link lifecycle webhooks."
)
async def receive_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Read the raw HTTP request body BEFORE any JSON parsing
    raw_body: bytes = await request.body()

    # 2. Extract Razorpay Security and Idempotency Headers
    signature = (
        request.headers.get("X-Razorpay-Signature") or
        request.headers.get("x-razorpay-signature")
    )
    event_id = (
        request.headers.get("X-Razorpay-Event-Id") or
        request.headers.get("x-razorpay-event-id")
    )

    # 3. Process Webhook through verified processor
    try:
        result = webhook_processor.process_webhook(
            db=db,
            raw_body=raw_body,
            signature=signature,
            event_id=event_id
        )
        return result
    except WebhookProcessingError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail=err.message
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing webhook: {str(exc)}"
        )
