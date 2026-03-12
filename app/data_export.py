import streamlit as st
import pandas as pd
import datetime
import io

from core.database import (
    get_all_food_logs,
    get_all_exercise_logs,
    get_all_hydration_logs,
    get_all_weight_logs,
    get_all_micronutrient_logs,
    get_user_by_id,
    get_streak_and_totals,
    get_micronutrient_summary,
)


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _build_pdf_bytes(uid: int) -> bytes:
    """Build a text-based PDF report using only standard library."""
    user = get_user_by_id(uid) or {}
    stats = get_streak_and_totals(uid)
    food_logs = get_all_food_logs(uid)
    exercise_logs = get_all_exercise_logs(uid)
    weight_logs = get_all_weight_logs(uid)
    micro_summary = get_micronutrient_summary(uid, days=30)

    lines = []
    lines.append("=" * 60)
    lines.append("NUTRILENS HEALTH REPORT")
    lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    # User Profile
    lines.append("")
    lines.append("--- USER PROFILE ---")
    lines.append(f"Name:     {user.get('name', 'N/A')}")
    lines.append(f"Age:      {user.get('age', 'N/A')}")
    lines.append(f"Gender:   {user.get('gender', 'N/A')}")
    lines.append(f"Weight:   {user.get('weight_kg', 'N/A')} kg")
    lines.append(f"Height:   {user.get('height_cm', 'N/A')} cm")
    lines.append(f"BMI:      {user.get('bmi', 0):.1f}")
    lines.append(f"Goal:     {user.get('daily_goal', 2000)} kcal/day")
    lines.append(f"Diet:     {user.get('diet', 'N/A')}")

    # Stats
    lines.append("")
    lines.append("--- PROGRESS STATS ---")
    lines.append(f"Total food entries: {stats['total_entries']}")
    lines.append(f"Total calories logged: {stats['total_cals']}")
    lines.append(f"Active days: {stats['active_days']}")
    lines.append(f"Current streak: {stats['streak']} days")

    # Recent Food Logs (last 50)
    lines.append("")
    lines.append("--- RECENT FOOD LOGS (last 50) ---")
    lines.append(f"{'Date':<20} {'Food':<25} {'Cals':>6} {'C':>5} {'P':>5} {'F':>5} {'Meal':<10}")
    lines.append("-" * 80)
    for log in food_logs[-50:]:
        lines.append(
            f"{log.get('logged_at', ''):<20} {log['name'][:24]:<25} "
            f"{log['calories']:>6} {log['carbs']:>5} {log['protein']:>5} "
            f"{log['fat']:>5} {log.get('meal', ''):<10}"
        )

    # Exercise Logs (last 30)
    lines.append("")
    lines.append("--- RECENT EXERCISE LOGS (last 30) ---")
    lines.append(f"{'Date':<20} {'Activity':<25} {'Min':>5} {'Burned':>8} {'Intensity':<10}")
    lines.append("-" * 70)
    for log in exercise_logs[-30:]:
        lines.append(
            f"{log.get('logged_at', ''):<20} {log['activity_name'][:24]:<25} "
            f"{log['duration_min']:>5} {log['calories_burned']:>8} "
            f"{log.get('intensity', ''):<10}"
        )

    # Weight History (last 20)
    lines.append("")
    lines.append("--- WEIGHT HISTORY (last 20) ---")
    lines.append(f"{'Date':<20} {'Weight (kg)':>12}")
    lines.append("-" * 35)
    for log in weight_logs[-20:]:
        lines.append(f"{log.get('logged_at', ''):<20} {log['weight_kg']:>12.1f}")

    # Micronutrient Summary
    if micro_summary:
        lines.append("")
        lines.append("--- MICRONUTRIENT SUMMARY (last 30 days) ---")
        lines.append(
            f"{'Day':<12} {'Iron':>8} {'Calcium':>8} {'VitC':>8} "
            f"{'VitD':>8} {'Fiber':>8} {'Sodium':>8} {'Sugar':>8}"
        )
        lines.append("-" * 80)
        for row in micro_summary:
            lines.append(
                f"{row['day']:<12} {row['iron']:>8.1f} {row['calcium']:>8.1f} "
                f"{row['vitamin_c']:>8.1f} {row['vitamin_d']:>8.1f} "
                f"{row['fiber']:>8.1f} {row['sodium']:>8.1f} {row['sugar']:>8.1f}"
            )

    lines.append("")
    lines.append("=" * 60)
    lines.append("End of NutriLens Report")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    # Build a minimal valid PDF
    return _text_to_pdf(report_text)


def _text_to_pdf(text: str) -> bytes:
    """Create a minimal PDF from plain text using only standard library."""
    lines = text.split("\n")
    # Build PDF content streams
    buf = io.BytesIO()

    # Mapping for escaping special PDF chars
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # We'll create a simple single-stream PDF
    content_lines = []
    y = 800
    page_contents = []
    current_page = []

    for line in lines:
        if y < 40:
            page_contents.append(current_page)
            current_page = []
            y = 800
        current_page.append((y, _esc(line[:95])))  # limit line length
        y -= 12

    if current_page:
        page_contents.append(current_page)

    # Build PDF objects
    objects = []
    obj_id = 1

    # Object 1: Catalog
    catalog_id = obj_id
    obj_id += 1
    # Object 2: Pages
    pages_id = obj_id
    obj_id += 1
    # Object 3: Font
    font_id = obj_id
    obj_id += 1

    # Page objects
    page_ids = []
    content_ids = []
    for _ in page_contents:
        page_ids.append(obj_id)
        obj_id += 1
        content_ids.append(obj_id)
        obj_id += 1

    # Write PDF
    buf.write(b"%PDF-1.4\n")
    offsets = {}

    # Catalog
    offsets[catalog_id] = buf.tell()
    buf.write(f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_id} 0 R >>\nendobj\n".encode())

    # Pages
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    offsets[pages_id] = buf.tell()
    buf.write(f"{pages_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\nendobj\n".encode())

    # Font
    offsets[font_id] = buf.tell()
    buf.write(f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n".encode())

    # Pages and content streams
    for i, page_lines in enumerate(page_contents):
        # Content stream
        stream_lines = ["BT", f"/F1 9 Tf"]
        for y_pos, text_line in page_lines:
            stream_lines.append(f"1 0 0 1 30 {y_pos} Tm")
            stream_lines.append(f"({text_line}) Tj")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)
        stream_bytes = stream_data.encode("latin-1", errors="replace")

        offsets[content_ids[i]] = buf.tell()
        buf.write(f"{content_ids[i]} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode())
        buf.write(stream_bytes)
        buf.write(b"\nendstream\nendobj\n")

        # Page object
        offsets[page_ids[i]] = buf.tell()
        buf.write(
            f"{page_ids[i]} 0 obj\n"
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 612 842] "
            f"/Contents {content_ids[i]} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n"
            f"endobj\n".encode()
        )

    # Cross-reference table
    xref_offset = buf.tell()
    total_objs = obj_id
    buf.write(b"xref\n")
    buf.write(f"0 {total_objs}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for oid in range(1, total_objs):
        off = offsets.get(oid, 0)
        buf.write(f"{off:010d} 00000 n \n".encode())

    buf.write(b"trailer\n")
    buf.write(f"<< /Size {total_objs} /Root {catalog_id} 0 R >>\n".encode())
    buf.write(b"startxref\n")
    buf.write(f"{xref_offset}\n".encode())
    buf.write(b"%%EOF\n")

    return buf.getvalue()


def render_data_export():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>📤 Data Export</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Export your health data as CSV or PDF reports.")
    st.write("---")

    user = get_user_by_id(uid) or {}
    username = user.get("name", "user")

    tab_csv, tab_pdf = st.tabs(["📊 CSV Export", "📄 PDF Report"])

    with tab_csv:
        st.markdown("### Download Individual Datasets")

        datasets = {
            "Food Logs": ("food_logs", get_all_food_logs),
            "Exercise Logs": ("exercise_logs", get_all_exercise_logs),
            "Hydration Logs": ("hydration_logs", get_all_hydration_logs),
            "Weight History": ("weight_logs", get_all_weight_logs),
            "Micronutrient Logs": ("micronutrient_logs", get_all_micronutrient_logs),
        }

        cols = st.columns(len(datasets))
        for i, (label, (filename, fetch_fn)) in enumerate(datasets.items()):
            data = fetch_fn(uid)
            count = len(data)
            with cols[i]:
                st.markdown(
                    f"<div style='text-align:center; padding:15px; background:#1e1e1e; "
                    f"border-radius:12px; border:1px solid #333;'>"
                    f"<h4 style='color:#00E676; margin:0;'>{label}</h4>"
                    f"<p style='color:#888; margin:5px 0;'>{count} records</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if data:
                    df = pd.DataFrame(data)
                    csv_bytes = _df_to_csv_bytes(df)
                    st.download_button(
                        f"⬇️ {label}",
                        data=csv_bytes,
                        file_name=f"nutrilens_{filename}_{username}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.caption("No data yet")

        # Combined export
        st.write("---")
        st.markdown("### 📦 Export All Data (Combined CSV)")
        if st.button("Generate Combined CSV", use_container_width=True):
            all_dfs = {}
            for label, (filename, fetch_fn) in datasets.items():
                data = fetch_fn(uid)
                if data:
                    all_dfs[filename] = pd.DataFrame(data)

            if all_dfs:
                output = io.BytesIO()
                # Write each dataset as a section
                combined = io.StringIO()
                for name, df in all_dfs.items():
                    combined.write(f"=== {name.upper()} ===\n")
                    combined.write(df.to_csv(index=False))
                    combined.write("\n\n")

                st.download_button(
                    "⬇️ Download Combined CSV",
                    data=combined.getvalue().encode("utf-8"),
                    file_name=f"nutrilens_all_data_{username}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.info("No data to export.")

    with tab_pdf:
        st.markdown("### 📄 Generate Health Report (PDF)")
        st.markdown(
            "Generate a comprehensive PDF report including your profile, food logs, "
            "exercise history, weight trends, and micronutrient summary."
        )

        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Building your report..."):
                pdf_bytes = _build_pdf_bytes(uid)

            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"nutrilens_report_{username}_{datetime.date.today().isoformat()}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("Report generated! Click above to download. 📥")

        # Preview section
        st.write("---")
        st.markdown("### 📊 Report Preview")
        stats = get_streak_and_totals(uid)
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Total Entries", stats["total_entries"])
        pc2.metric("Active Days", stats["active_days"])
        pc3.metric("Current Streak", f"{stats['streak']} days")
        pc4.metric("Lifetime Calories", f"{stats['total_cals']:,}")
