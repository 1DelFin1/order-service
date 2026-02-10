from fastapi import HTTPException, status


PRODUCT_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
)

REVIEW_NOT_FOUND_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
)

REVIEW_ALREADY_EXISTS_EXCEPTION = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="User has already reviewed this product"
)
