import frappe
from frappe import _
from frappe.email.doctype.notification.notification import Notification, get_context, json
from frappe.core.doctype.role.role import get_info_based_on_role, get_user_info
import requests
import json
import io
import base64
# to send whatsapp message and document using ultramsg
class ERPGulfNotification(Notification):
 #to create pdf
  def create_pdf(self,doc):
      file = frappe.get_print(doc.doctype, doc.name, self.print_format, as_pdf=True)
      pdf_bytes = io.BytesIO(file)
      pdf_base64 = base64.b64encode(pdf_bytes.getvalue()).decode()
      in_memory_url = f"data:application/pdf;base64,{pdf_base64}"
      return in_memory_url
     
 # fetch pdf from the create_pdf function and send to whatsapp     
  def send_whatsapp_with_pdf(self,doc,context):
      memory_url = self.create_pdf(doc)
      token = frappe.get_doc('whatsapp message').get('token') 
      msg1 = frappe.render_template(self.message, context)
      recipients = self.get_receiver_list(doc,context)
    #   receiverNumbers = []
      for receipt in recipients:
        number = receipt
      document_url= frappe.get_doc('whatsapp message').get('url')
      payload = {
        'token': token,
        'to':number,
        "filename": doc.name,
        "document": memory_url,
        "caption": msg1,
         }
      headers = {'content-type': 'application/x-www-form-urlencoded'} 
 
      try:
          response = requests.post(document_url, data=payload, headers=headers)
          
          return response.text
      except Exception as e:
          return e
      
  #send message without pdf
  def send_whatsapp_without_pdf(self,doc,context):
    token = frappe.get_doc('whatsapp message').get('token') 
    message_url =  frappe.get_doc('whatsapp message').get('message_url')
    msg1 = frappe.render_template(self.message, context)
    recipients = self.get_receiver_list(doc,context)
    # receiverNumbers = []
    for receipt in recipients:
        number = receipt
  
    payload = {
        'token': token,
        'to':number,
        'body':msg1,
       }
       
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(message_url, data=payload, headers=headers)
        return response.text
    except Exception as e:
        return e
  
    
  # call the  send whatsapp with pdf function and send whatsapp without pdf function and it work with the help of condition 
  def send(self, doc):
      context = {"doc":doc, "alert": self, "comments": None}
      if doc.get("_comments"):
        context["comments"] = json.loads(doc.get("_comments"))
      if self.is_standard:
        self.load_standard_properties(context)
            
      try:
            if self.channel == "whatsapp message":
              # if attach_print and print format both are working then it send pdf with message
                if self.attach_print and self.print_format:
                    i= self.send_whatsapp_with_pdf(doc,context)
               # otherwise only message will send     
                else:
                    i=self.send_whatsapp_without_pdf(doc,context)
        
      except:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())  
      super(ERPGulfNotification, self).send(doc)
                       
                       
  def get_receiver_list(self, doc, context):
    """return receiver list based on the doc field and role specified"""
    receiver_list = []
    for recipient in self.recipients:
            if recipient.condition:
                if not frappe.safe_eval(recipient.condition, None, context):
                    continue
			# For sending messages to the owner's mobile phone number
            if recipient.receiver_by_document_field == "owner":
                    receiver_list += get_user_info([dict(user_name=doc.get("owner"))], "mobile_no")
			# For sending messages to the number specified in the receiver field
            elif recipient.receiver_by_document_field:
                    receiver_list.append(doc.get(recipient.receiver_by_document_field))
			# For sending messages to specified role
            if recipient.receiver_by_role:
                receiver_list += get_info_based_on_role(recipient.receiver_by_role, "mobile_no")
            return receiver_list
  
    
    
 