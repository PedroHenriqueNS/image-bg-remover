from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from rembg import remove, new_session
from PIL import Image
import uvicorn
import io
import os


app = FastAPI()
session = new_session("u2net")


# Health check endpoint (recommended for Render)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Main endpoint
@app.post("/remove-bg/")
async def remove_bg(file: UploadFile):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        processed_image = remove(image, session=session)

        output_buffer = io.BytesIO()
        processed_image.save(output_buffer, optimize=True,  format="PNG")
        output_buffer.seek(0)
        
        return StreamingResponse(
            output_buffer,
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=processed_image.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error when processing image: {str(e)}")
    

# Endpoint to receive and return image metadata
@app.post("/image-metadata/")
async def image_metadata(file: UploadFile):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    return {
        "filename": file.filename,
        "format": image.format,
        "size": image.size,
        "mode": image.mode
    }

# Configure for Render
if __name__ == "__main__":
    # Render uses PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)