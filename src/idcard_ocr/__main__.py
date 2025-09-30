"""Command line entry point for running the FastAPI server locally."""
import uvicorn


def main() -> None:
    uvicorn.run(
        "idcard_ocr.api.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )


if __name__ == "__main__":
    main()
