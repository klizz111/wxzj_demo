import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [patientInfo, setPatientInfo] = useState({
    gender: '男',
    age: '30',
    weight: '70',
  });
  const [description, setDescription] = useState('最近几天老是头痛，怕风，身上出汗但觉得冷，没胃口。');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('/test01.png');
  const [diagnosisResult, setDiagnosisResult] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 初始化时，如果有需要，可以预加载默认图片将其转为 File 给后端用
  // 为了确保首次提交不报错且带有测试图，我们可以通过 fetch 生成默认的 File 对象
  useEffect(() => {
    fetch('/test01.png')
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], 'test01.png', { type: 'image/png' });
        setImageFile(file);
      })
      .catch(err => console.error('默认图片加载失败', err));
  }, []);

  const handleInfoChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setPatientInfo((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setDiagnosisResult('正在诊断中，请稍候...\n');

    try {
      // Create FormData to send the data as mentioned in sum02.md
      const formData = new FormData();
      formData.append('description', description);
      if (imageFile) {
        formData.append('image', imageFile);
      }
      formData.append('stream', 'true');

      // Fetch real endpoint
      const response = await fetch('http://localhost:8000/api/chat/diagnosis', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`服务器响应错误: ${response.status}`);
      }

      setDiagnosisResult('');

      if (!response.body) {
        throw new Error('未获取到响应流');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        // The SSE payload might come as "data: {content...}\n\n", or just raw text.
        // If it's pure chunks yielded from the backend SSE without 'data:', it will append correctly.
        setDiagnosisResult((prev) => prev + text);
      }

    } catch (err: any) {
      console.error(err);
      setDiagnosisResult(`连接服务器或解析错误: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>五行知己 - AI 中医诊疗系统</h1>
      </header>

      <main className="main-content">
        <form onSubmit={handleSubmit} className="diagnostic-form">
          <section className="form-section">
            <h2>基本信息</h2>
            <div className="form-group row">
              <label>
                <span>性别:</span>
                <select name="gender" value={patientInfo.gender} onChange={handleInfoChange}>
                  <option value="男">男</option>
                  <option value="女">女</option>
                  <option value="其他">其他</option>
                </select>
              </label>
              <label>
                <span>年龄 (岁):</span>
                <input type="number" name="age" value={patientInfo.age} onChange={handleInfoChange} />
              </label>
              <label>
                <span>体重 (kg):</span>
                <input type="number" name="weight" value={patientInfo.weight} onChange={handleInfoChange} />
              </label>
            </div>
          </section>

          <section className="form-section">
            <h2>症状描述</h2>
            <div className="form-group">
              <textarea
                className="symptoms-input"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="请详细描述您的症状..."
                required
              />
            </div>
          </section>

          <section className="form-section">
            <h2>舌诊上传 (可选)</h2>
            <div className="form-group image-upload">
              {/* 图片预览区 */}
              {imagePreview && (
                <div className="image-preview-container">
                    <img src={imagePreview} alt="舌诊图片预览" className="preview-img" />
                </div>
              )}
              <input
                type="file"
                accept="image/*"
                ref={fileInputRef}
                onChange={handleImageChange}
                className="file-input"
              />
              {imageFile && <p className="file-name">已选择: {imageFile.name}</p>}
            </div>
          </section>

          <div className="form-actions">
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? '诊断中...' : '开始诊断'}
            </button>
          </div>
        </form>

        <section className="result-section">
          <h2>诊断结果</h2>
          <div className="result-box">
            {diagnosisResult ? (
              <ReactMarkdown>{diagnosisResult}</ReactMarkdown>
            ) : (
              <p className="placeholder-text">点击“开始诊断”以获取分析结果。</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
