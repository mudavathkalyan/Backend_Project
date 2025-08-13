

const registerUser=async(req,res)=>{
    try {
        res.status(200).json({
            messsage:"oKk"
        })
    } catch (error) {
        console.log(error)
    }
}



export{registerUser}