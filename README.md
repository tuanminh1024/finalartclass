# Art Report Streamlit

Ứng dụng tạo PDF phiếu hoàn thành bài học mỹ thuật từ Google Sheets.

## Chạy local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Biến môi trường cần có
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## Deploy Render
- Kết nối repo GitHub
- Thêm env var `GOOGLE_SERVICE_ACCOUNT_JSON`
- Deploy bằng `render.yaml`

## Lưu ý
- Share Google Sheet cho email service account
- Cần đặt font vào thư mục `assets/`
- Cần tự thêm 2 file font: `assets/NotoSans-Regular.ttf` và `assets/NotoSans-Bold.ttf`
