import pandas as pd
import smtplib as sm
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
data =pd.read_excel("Data.xlsx", sheet_name="A")

# email_col=data.iloc[:,3]
# list_of_emails= list(email_col)
# print(list_of_emails)


# email_col="_____.ac.in", "_______@gmail.com"
# list_of_emails= list(email_col)
# print(list_of_emails)

try:
    from_ = '______@gmail.com'
    to_= 'list_of_emails'
    message = MIMEMultipart('alternative')
    message['Subject'] = '___________'
    message['From'] = '_______@gmail.com'
# creating the text
    html='''
    
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Placement Invitation</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      margin: 20px;
      color: #333;
    }
    h1, h2, h3 {
      color: #004080;
    }
    .highlight {
      background-color: #f0f8ff;
      padding: 10px;
      border-left: 5px solid #004080;
      margin: 15px 0;
    }
    .contact {
      margin-top: 20px;
      padding: 10px;
      border: 1px solid #ccc;
      background-color: #fafafa;
    }
  </style>
</head>
<body>

  <h1>M</h1>
  <p><em>Dear Recruiter,</em></p>

  <p>Warmest greetings of the season to you from .</p>

  <p>
    It gives me immense pleasure to apprise you that the final year batch of B.Tech, M.Tech, M.Sc and Ph.D students 
    in the following disciplines are:
  </p>

  <ul>
    <li>Civil Engineering</li>
    <li>Computer Science and Engineering</li>
    <li>Electrical and Electronics Engineering</li>
    <li>Mechanical Engineering</li>
    <li>Physics</li>
    <li>Chemical and Biological Sciences</li>
  </ul>

  <p>They will be respectively.</p>

  <h2>Placement Highlights</h2>

  <div class="highlight">
    <p><strong>Placement Brochure</strong></p>
  </div>

  <p>
     X has firmly established itself as a premier institute of repute and center of excellence in 
    the fields of engineering and scientific research. 
  </p>

  <p>
    We are glad to inform you that while topping the XXXX, the Institute stands at 
    <strong>14th among all the XXXX</strong> of the country and <strong>2nd among all the XXXX</strong>. 
    Recently, the Institute has been ranked <strong> XXXX among government engineering colleges</strong> 
    by the India Today Magazine.
  </p>

  <p>
    In an effort to bridge the gap between academia and industry, the institute promotes industry-academia 
    interface to acquaint the students with the latest industry trends and emerging cutting-edge technologies. 
    students to real-world challenges and offer opportunities to utilize their academic knowledge and demonstrate 
    their problem-solving skills.
  </p>

  <p>
    We have excellent infrastructure and are well equipped with requisite state-of-the-art amenities to conduct 
    campus placement activities, viz. parallel interview sessions, pre-placement talks, group discussions, etc.
  </p>

  <p>
    We are well equipped with all the necessary amenities to conduct the recruitment drives through various AV 
    modes as per the convenience of our esteemed recruiters in the prevailing uncertain times in the wake of the outbreak of the pandemic.
  </p>

  <p>
    We cordially invite your esteemed organization to visit our institute and participate in the hiring process 
    through modes of your convenience.
  </p>

  <p>
    We request you to please fill out our Job Notification Form to move ahead with the process.
  </p>

  <h3>Thank you,</h3>
  <p>Training and Placement Team</p>

  <div class="contact">
    <h3>Get in touch</h3>
    <p><strong>mr. </strong><br>
       Placement <br>
       C<br>
       📞 +91
    </p>

    <p><strong>Dr. </strong><br>
       in-charge,<br>
       C<br>
       ✉ placement<br>
       CC
    </p>
  </div>

  <h3>Thanks and Regards,</h3>
  <p>
    ------------------------------------<br><br>
    <strong>B</strong><br>
    C<br>
    Centre<br>
    N<br>
    Tel: +91 
  </p>

  <p>
    For<br><br>
    <strong>Dr.</strong><br>
    in-charge,<br>
    C<br>
    N<br>
    ✉ v<br>
    📞 
  </p>

</body>
</html>

    
    '''
    # send the message
    #object of smtp
    context = ssl.create_default_context()
    with sm.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    # server.starttls()
    #login
        smtp.login('____@gmail.com', '_________')
        text = MIMEText(html,"html")
        message.attach(text)
        to_ = "__________"
        smtp.sendmail(from_, to_, message.as_string())
    print('message sent')

except Exception as e:
    print(e)