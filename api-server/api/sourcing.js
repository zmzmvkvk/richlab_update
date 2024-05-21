const { spawn } = require('child_process');

async function runSourcing(bufferData, res, user) {
    // 사용자 데이터를 JSON 문자열로 변환
    const userString = JSON.stringify(user);
    
    const pythonProcess = spawn('python3', ['./python/sourcing.py', userString]);

    pythonProcess.stdin.write(bufferData);
    pythonProcess.stdin.end();

    let output = '';
    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.log(`Python script exited with code ${code}`);
            return res.status(500).send('Python script error');
        }
        res.send(`Python Output: ${output}`);
    });
}

module.exports = { runSourcing };