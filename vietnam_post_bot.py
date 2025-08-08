# vietnam_post_bot.py
import streamlit as st
import google.generativeai as genai
import os
import re
import random
from dotenv import load_dotenv

# --- PHẦN 1: CẤU HÌNH VÀ CHUẨN BỊ DỮ LIỆU ---

# Tải API key từ file .env
load_dotenv()
GEMMA_API_KEY = os.getenv("GEMMA_API_KEY")

# Cấu hình API key của Google
try:
    genai.configure(api_key=GEMMA_API_KEY)
    model = genai.GenerativeModel('models/gemma-3-27b-it')
except (ValueError, TypeError) as e:
    st.error("LỖI: Không tìm thấy hoặc API Key không hợp lệ. Vui lòng kiểm tra file .env của bạn.")
    st.stop()

# Lưu trữ các tùy chọn
MUC_DICH_OPTIONS = {
    1: "Giới thiệu và làm rõ lợi ích của dịch vụ cho khách hàng chưa biết.",
    2: "Tăng cường tương tác (like, comment, share) và xây dựng cộng đồng.",
    3: "Kêu gọi hành động cụ thể (ví dụ: tải app, đến bưu cục gần nhất, đăng ký dịch vụ).",
    4: "Xây dựng hình ảnh thương hiệu Bưu điện gần gũi, đáng tin cậy.",
    5: "Chia sẻ câu chuyện thành công của khách hàng (case study/testimonial) để tăng uy tín.",
    6: "Giải đáp thắc mắc thường gặp và cung cấp các mẹo hữu ích cho khách hàng.",
}

GIONG_VAN_OPTIONS = {
    1: "Chuyên nghiệp & Đáng tin cậy: Nhấn mạnh vào sự an toàn, quy trình rõ ràng, minh bạch.",
    2: "Thân thiện & Gần gũi: Dùng ngôn từ đơn giản, dễ hiểu, như một người bạn.",
    3: "Vui vẻ & Bắt trend: Sử dụng các từ ngữ, cấu trúc câu đang thịnh hành.",
    4: "Truyền cảm hứng & Kể chuyện: Chia sẻ một câu chuyện ý nghĩa.",
    5: "Đồng cảm & Thấu hiểu: Tập trung vào việc giải quyết các nỗi lo của khách hàng.",
    6: "Chia sẻ kiến thức & Hướng dẫn: Cung cấp thông tin hữu ích, mẹo vặt.",
}

# Khung prompt mẫu
MASTER_PROMPT_TEMPLATE = """
# BỐI CẢNH VÀ VAI TRÒ
BẠN LÀ: Một chuyên gia sáng tạo nội dung Social Media, am hiểu sâu sắc về thị trường Việt Nam và có chuyên môn về các sản phẩm, dịch vụ của Bưu điện Việt Nam (Vietnam Post).
MỤC TIÊU CỦA BẠN: Giúp tôi, một nhân viên Bưu điện, tạo ra một bài viết đăng trên Facebook thật hấp dẫn, chuyên nghiệp và hiệu quả dựa trên các thông tin tôi cung cấp dưới đây.

# THÔNG TIN CHI TIẾT VỀ BÀI VIẾT
Dưới đây là các thông tin cần thiết, hãy dựa vào đây để tạo bài viết:

**1. Sản phẩm/Dịch vụ cốt lõi:**
{san_pham}

**2. Mục đích chính của bài viết:**
{muc_dich}

**3. Giọng văn mong muốn:**
{giong_van}

**4. Các điểm nhấn hoặc thông tin quan trọng khác:**
{diem_nhan}

# YÊU CẦU VỀ ĐỊNH DẠNG ĐẦU RA
- **Kết quả cuối cùng:** Phải là MỘT bài viết hoàn chỉnh, liền mạch, sẵn sàng để sao chép và đăng trực tiếp lên Facebook.
- **Cấu trúc:** Bài viết phải có 3 phần rõ ràng:
    1.  **Câu Mở Đầu (Hook):** Phải thật ấn tượng, thu hút sự chú ý trong 3 giây đầu tiên (có thể là câu hỏi, một sự thật gây ngạc nhiên, hoặc một vấn đề mà khách hàng đang gặp).
    2.  **Nội dung chính:** Diễn giải các lợi ích một cách rõ ràng, dễ hiểu. Sử dụng icon (biểu tượng cảm xúc) một cách tinh tế để tăng tính sinh động và phân tách các ý. Có thể dùng gạch đầu dòng/đánh số để liệt kê.
    3.  **Kêu Gọi Hành Động (Call-to-Action):** Phải thật rõ ràng và thôi thúc.
- **TUYỆT ĐỐI KHÔNG** được chứa các tiêu đề phân mục như "Câu Mở Đầu (Hook):", "Nội dung chính:", "Kêu gọi hành động:".
- **Hashtag:** **BẮT BUỘC** có hashtag #VNP, đề xuất thêm 3-4 hashtag phù hợp, bao gồm hashtag thương hiệu, hashtag dịch vụ và hashtag xu hướng (nếu có).
- **BẮT BUỘC** trong phần "3. **Kêu Gọi Hành Động (Call-to-Action):**" phải kết hợp thêm thông tin liên hệ sau: {thong_tin_lien_he}
"""

# --- PHẦN 2: HÀM LOGIC VÀ THIẾT KẾ GIAO DIỆN ---

def generate_post(san_pham, diem_nhan, lien_he):
    """Hàm xử lý việc tạo bài viết."""
    if not san_pham or not lien_he:
        st.warning("Vui lòng điền đầy đủ thông tin 'Sản phẩm/Dịch vụ' và 'Thông tin liên hệ'.")
        return

    with st.spinner("Chuyên gia đang sáng tạo, vui lòng chờ trong giây lát... ✍️"):
        try:
            # Tự động chọn ngẫu nhiên mục đích và giọng văn
            random_muc_dich = random.choice(list(MUC_DICH_OPTIONS.values()))
            random_giong_van = random.choice(list(GIONG_VAN_OPTIONS.values()))

            # Điền thông tin vào khung prompt
            final_prompt = MASTER_PROMPT_TEMPLATE.format(
                san_pham=san_pham,
                muc_dich=random_muc_dich,
                giong_van=random_giong_van,
                diem_nhan=diem_nhan or "Không có",
                thong_tin_lien_he=lien_he
            )
            
            # Gửi prompt hoàn chỉnh đến Gemma
            response = model.generate_content(final_prompt)
            
            # Lưu kết quả vào session state
            st.session_state['generated_text'] = response.text
            st.session_state['show_result'] = True

        except Exception as e:
            st.error(f"Đã có lỗi xảy ra khi tạo bài viết: {e}")
            st.session_state['show_result'] = False

# --- Giao diện chính ---
st.set_page_config(page_title="Trợ lý Viết bài Bưu điện", page_icon="📮", layout="wide")

# --- MÃ GOOGLE ANALYTICS ---
# Sử dụng st.html() để chèn mã vào phần đầu của trang một cách đáng tin cậy hơn
st.html("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-85N4WR4EB7"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-85N4WR4EB7');
</script>
""")
# -------------------------

st.title("📮 Trợ lý Sáng tạo Nội dung Vietnam Post")
st.caption("Chỉ cần điền 3 thông tin dưới đây, AI sẽ giúp bạn tạo ra một bài viết Facebook hoàn chỉnh!")

# Khởi tạo session_state
if 'generated_text' not in st.session_state:
    st.session_state['generated_text'] = ""
if 'show_result' not in st.session_state:
    st.session_state['show_result'] = False

# --- Vùng nhập liệu ---
with st.container(border=True):
    st.subheader("1. Cung cấp thông tin cần thiết")
    san_pham_input = st.text_input(
        "**Sản phẩm/Dịch vụ cốt lõi:**",
        placeholder="Ví dụ: Bảo hiểm xe máy PTI, Chuyển phát nhanh EMS..."
    )
    diem_nhan_input = st.text_area(
        "**Các điểm nhấn hoặc thông tin quan trọng khác:** (Không bắt buộc)",
        placeholder="Ví dụ: Chương trình giảm giá 20%, Miễn phí tạo tài khoản..."
    )
    lien_he_input = st.text_input(
        "**Thông tin liên hệ:**",
        placeholder="Ví dụ: 0988.888.888 - Nguyễn Văn A - Bưu cục ABC"
    )

    # Nút tạo bài viết
    st.button(
        "Tạo bài viết ✨",
        on_click=generate_post,
        args=(san_pham_input, diem_nhan_input, lien_he_input),
        type="primary",
        use_container_width=True
    )

# --- Vùng hiển thị kết quả ---
if st.session_state['show_result'] and st.session_state['generated_text']:
    with st.container(border=True):
        st.subheader("2. Kết quả")
        st.markdown(st.session_state['generated_text'])
        
        st.divider()

        st.subheader("3. Thao tác")
        # Nút "Tạo lại"
        st.button(
            "Tạo lại 🔄",
            on_click=generate_post,
            args=(san_pham_input, diem_nhan_input, lien_he_input),
            use_container_width=True,
            key="regenerate_button"
        )
        
        # Hướng dẫn và khu vực sao chép đáng tin cậy
        st.success("**Để sao chép bài viết, hãy nhấn vào biểu tượng 📋 ở góc trên bên phải của khung dưới đây.**")
        st.code(st.session_state['generated_text'], language=None)
