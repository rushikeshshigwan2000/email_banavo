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
        server.mail('test@example.com')
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
st.title("Ye chal email banate hai")
st.write("ye bhidu!  teri file idhar UPLOAD kar na")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'Email' in df.columns:
        st.write("### Uploaded Data")
        st.dataframe(df.head())
        
        if st.button("Validate Emails"):
            result_df = validate_emails(df)
            st.write("### Validation Results")
            st.dataframe(result_df)
            
            # Save results to CSV
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            result_df.to_csv(temp_file.name, index=False)
            
            # Provide download link
            with open(temp_file.name, "rb") as file:
                st.download_button("Download Results as CSV", file, "validated_emails.csv", "text/csv")
    else:
        st.error("CSV file must contain an 'Email' column.")
