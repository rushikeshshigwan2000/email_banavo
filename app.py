import streamlit as st
import pandas as pd
import smtplib
import dns.resolver
import tempfile

def extract_domain(email):
    """Extracts domain from an email."""
    try:
        return email.split("@")[1]
    except IndexError:
        return None

def is_domain_valid(domain):
    """Checks if the domain has MX records."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return True if mx_records else False
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout):
        return False

def is_email_valid(email, domain):
    """Validates email using SMTP by checking the recipient."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)

        # Connect to SMTP server
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_record)
        server.helo()
        server.mail('noreply@datagateway.in')
        code, message = server.rcpt(email)
        server.quit()

        return code == 250  # 250 means the email exists
    except Exception:
        return False

def validate_emails(df):
    """Validates emails in a DataFrame and returns results."""
    results = []
    for email in df['Email']:
        domain = extract_domain(email)
        if domain:
            domain_status = is_domain_valid(domain)
            email_status = is_email_valid(email, domain) if domain_status else False
            results.append([email, domain, domain_status, email_status])
        else:
            results.append([email, None, False, False])
    return pd.DataFrame(results, columns=['Email', 'Domain', 'Domain Valid', 'Email Valid'])

# Streamlit UI
# Center align title using Markdown and HTML
st.markdown("<h1 style='text-align: center;'>Email Checker</h1>", unsafe_allow_html=True)




# Single Email Validation Input
single_email = st.text_input("Enter a single email to validate")
if st.button("Validate Email"):
    if single_email:
        domain = extract_domain(single_email)
        if domain:
            domain_status = is_domain_valid(domain)
            email_status = is_email_valid(single_email, domain) if domain_status else False
            st.write(f"**Email:** {single_email}")
            st.write(f"**Domain:** {domain}")
            st.write(f"**Domain Valid:** {'✅' if domain_status else '❌'}")
            st.write(f"**Email Valid:** {'✅' if email_status else '❌'}")
        else:
            st.error("Invalid email format. Please enter a valid email.")
    else:
        st.error("Please enter an email to validate.")
        
st.write("Upload your Excel file here")

uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(uploaded_file)
    elif file_extension == "xlsx":
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file format. Please upload a CSV or Excel file.")
        st.stop()
    
    if 'Email' in df.columns:
        st.write("### Uploaded Data")
        st.dataframe(df.head())
        
        if st.button("Validate Emails"):
            result_df = validate_emails(df)
            st.write("### Validation Results")
            st.dataframe(result_df)
            
            # Save results to CSV
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            result_df.to_csv(temp_csv.name, index=False)
            
            # Save results to Excel
            temp_xlsx = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            with pd.ExcelWriter(temp_xlsx.name, engine='xlsxwriter') as writer:
                result_df.to_excel(writer, index=False)
            
            # Provide download links
            with open(temp_csv.name, "rb") as file:
                st.download_button("Download Results as CSV", file, "validated_emails.csv", "text/csv")
            with open(temp_xlsx.name, "rb") as file:
                st.download_button("Download Results as Excel", file, "validated_emails.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("CSV or Excel file must contain an 'Email' column.")
