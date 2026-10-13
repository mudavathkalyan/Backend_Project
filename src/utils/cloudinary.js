import { v2 as cloudinary } from "cloudinary"
import fs from "fs"
import path from "path"

cloudinary.config({ 
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME, 
  api_key: process.env.CLOUDINARY_API_KEY, 
  api_secret: process.env.CLOUDINARY_API_SECRET 
});

const uploadOnCloudinary = async (localFilePath) => {
  try {
    if (!localFilePath) return null

    // Ensure absolute path
    const absolutePath = path.resolve(localFilePath)

    // Upload the file to Cloudinary
    const response = await cloudinary.uploader.upload(absolutePath, {
      resource_type: "auto"
    })

    // Remove local file after upload
    if (fs.existsSync(absolutePath)) {
      fs.unlinkSync(absolutePath)
    }

    return response;

  } catch (error) {
    console.error("Cloudinary upload error:", error)

    // Remove local file if exists
    if (localFilePath && fs.existsSync(localFilePath)) {
      fs.unlinkSync(localFilePath)
    }

    return null;
  }
}

export { uploadOnCloudinary }
