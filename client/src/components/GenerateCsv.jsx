import React from 'react';
import axios from "axios";

const GenerateCsv = () => {

  const handleGenerate = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);  // 이벤트 타겟으로부터 FormData 생성

    try {
      const response = await axios.post("/sourcing", formData, {
        headers: {
          'Content-Type': 'multipart/form-data'  // 적절한 Content-Type 설정
        }
      });
      console.log('Server response:', response.data);
    } catch (error) {
      console.error("CSV error:", error);
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
