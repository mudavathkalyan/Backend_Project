import { User } from "../models/user.model.js"
import { uploadOnCloudinary } from "../utils/cloudinary.js"

    // get user details from frontend
    // validation - not empty
    // check if user already exists: username, email
    // check for images, check for avatar
    // upload them to cloudinary, avatar
    // create user object - create entry in db
    // remove password and refresh token field from response
    // check for user creation
    // return res

const registerUser = async (req, res) => {

    const { fullName, email, username, password } = req.body;
    try {

        // if (!fullName || !email || !username || !password){
        //     return res.status(400).json({ message: "All Fields are Required" });
        // }

        // another Way
        if (
            [fullName, email, username, password].some((field) =>
                field?.trim() === ""
            )
        ) {
            return res.status(400).json({ message: "All Fields are Required" });
        }

        // check if user already exists: username, email
        const existingUser = await User.findOne({
            $or: [{ username }, { email }]
        })

        if (existingUser) {
            return res.status(400).json({ message: "User Already Exists" })
        }

        // check for images, check for avatar
        const avatarLocalPath = req.files?.avatar?.[0]?.path;

        let coverImageLocalPath;
        if (req.files && Array.isArray(req.files.coverImage) && req.files.coverImage.length > 0) {
            coverImageLocalPath = req.files.coverImage[0].path
        }

        if (!avatarLocalPath) {
            return res.status(400).json({ message: "Avatar Required" })
        }

        // upload them to cloudinary, avatar
        const avatar = await uploadOnCloudinary(avatarLocalPath)
        const coverImage = await uploadOnCloudinary(coverImageLocalPath)

        if (!avatar) {
            return res.status(400).json({ message: "Avatar upload failed" })
        }

        // create user object - create entry in db
        const user = await User.create({
            fullName,
            avatar: avatar.url,
            coverImage: coverImage?.url || "",
            email,
            password,
            username: username.toLowerCase()
        })

        // remove password and refresh token field from response
        const { password: _, refreshToken, ...safeUser } = user.toObject()

        // check for user creation
        if (!safeUser) {
            return res.status(500).json({ message: "Something went wrong while registering the user" })
        }

        // return res
        return res.status(201).json({
            message: "User created successfully",
            user: safeUser
        })

    } catch (error) {
        console.error(error)
        res.status(500).json({ message: "Internal Server Error", error: error.message })
    }
}

export { registerUser }
