import express from "express"
import cors from "cors"

import cookieParser from "cookie-parser"


const app=express();


app.use(cors({
    origin:process.env.CORS_ORIGIN,
    credentials:true
}));

//configurations

//accept json
app.use(express.json({limit:"20kb"}))

//accept url
app.use(express.urlencoded({limit:"20kb"}))

app.use(express.static("public"))

app.use(cookieParser())


// importing routes

import userRouter from './routes/user.routes.js'


//routes decleration
app.use('/api/v1/users',userRouter)


export {app}