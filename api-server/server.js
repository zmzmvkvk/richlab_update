require("dotenv").config();
const express = require("express");
const multer = require('multer');
const app = express();
const path = require("path");
const jwt = require("jsonwebtoken");
const JWT_SECRET = process.env.JWT_SECRET;
const PORT = process.env.PORT || 3000;
const storage = multer.memoryStorage(); // 메모리 스토리지를 사용
const upload = multer({ storage: storage });

// 모든 도메인에서의 접근을 허용하는 경우
const { runSourcing } = require('./api/sourcing.js');
app.use(express.static(path.join(__dirname, "../client/build")));

app.use(express.json()); // JSON 본문을 파싱하기 위해
app.use(express.urlencoded({ extended: true })); // 폼 데이터 본문을 파싱하기 위해

// JWT 검증 미들웨어`
const { MongoClient } = require("mongodb");
const dbUser = process.env.DB_USER;
const dbPassword = encodeURIComponent(process.env.DB_PASSWORD);
const dbName = "richlab";
const dburl = `mongodb+srv://${dbUser}:${dbPassword}@cluster0.xseitpb.mongodb.net/`;
let db;

new MongoClient(dburl)
    .connect()
    .then((client) => {
        console.log("DB연결성공");
        db = client.db(dbName);
        app.listen(PORT, (req, res) => {
            console.log(`server is runnung on localhost:${PORT}`)
        });
    })
    .catch((err) => {
        console.log(err);
    });

// JWT 검증 미들웨어
function authenticateToken(req, res, next) {
    const authHeader = req.headers["authorization"];
    const token = authHeader && authHeader.split(" ")[1]; // Bearer TOKEN 형식

    if (token == null) {
        return res.sendStatus(401); // Unauthorized
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.sendStatus(403); // Forbidden - Invalid Token
        }
        req.user = user;
        next();
    });
}

app.get("/verify-token", authenticateToken, (req, res) => {
    // 토큰 검증이 성공하면, 검증된 사용자 정보를 반환
    res.status(200).json({ message: "Token is valid", user: req.user });
});

app.post("/login", async (req, res) => {
    const { userid, userpw } = req.body;
    try {
        const user = await db.collection("user").findOne({ userid });
        if (user) {
            const token = jwt.sign({ userid: user.userid }, JWT_SECRET, {
                expiresIn: "3h",
            });
            res.status(200).json({ message: "Login successful", token });
        } else {
            res.status(401).json({ message: "Incorrect credentials" });
        }
    } catch (error) {
        console.error("Error in login:", error);
        res.status(500).json({ message: "Server error", error });
    }
});

// Python 스크립트 실행 경로 설정
app.post('/sourcing', upload.single("csvFile"), async (req, res) => {
    const csvFileBuffer = req.file.buffer;
    runSourcing(csvFileBuffer, res);
});

app.get("/", (req, res) => {
    res.sendFile(path.resolve(__dirname, "../client/build", "index.html"));
});