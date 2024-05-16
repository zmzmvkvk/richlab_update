import React from 'react';
import axios from "axios";

const GenerateCsv = () => {
  const handleGenerate = async (event) => {
    event.preventDefault();
    const data = new FormData(event.target);
    for (let key of data.keys()) {
      console.log(key, data.get(key));
    }
    try {
      const response = await axios.post("/sourcing", data); // 헤더 제거

      console.log('Server response:', response.data);
    } catch (error) {
      console.error("csv error:", error);
    }
  };

  return (
    <div>
      <form onSubmit={handleGenerate} encType="multipart/form-data">
        <input type="file" name="csvFile" />
        <button type="submit">클릭</button>
      </form>
    </div>
  );
}

export default GenerateCsv;
