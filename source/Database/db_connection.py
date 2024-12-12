import pyodbc  

class DBConnection:
    def __init__(self,server_name):
        self.server_name=server_name

    def Get_DB_Connection(self):
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};' ## or ODBC Driver 17 for SQL Server
            f'SERVER={self.server_name};'
            'DATABASE=Law_ChatBot_DB;'
            'Trusted_Connection=yes;'
        )

        return conn
    
    def Create_Session(self):
        conn = self.Get_DB_Connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO Chat_Sessions (create_at) OUTPUT INSERTED.id VALUES (GETDATE())")
        
        session_id = cursor.fetchone()[0]  
        conn.commit()  
        conn.close()  

        return session_id 
    
    def Insert_Message(self,session_id,sender,message):
        conn = self.Get_DB_Connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO Chat_Messages (session_id, sender, message, send_at)
            VALUES (?, ?, ?, GETDATE())
            """,
            (session_id, sender, message)
        )

        conn.commit()  
        conn.close()  

    def Get_Session(self):
        conn = self.Get_DB_Connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            cs.id, 
            cs.create_at, 
            (SELECT TOP 1 message FROM Chat_Messages 
            WHERE session_id = cs.id AND sender = 'user' 
            ORDER BY send_at ASC) AS first_message
        FROM Chat_Sessions cs
        WHERE EXISTS (
            SELECT 1 FROM Chat_Messages 
            WHERE session_id = cs.id AND sender = 'user'
        )
        ORDER BY cs.create_at DESC
        """
        
        cursor.execute(query)
        sessions = cursor.fetchall()
        conn.close()

        return  sessions
    
    def Get_History(self,session_id):
        conn = self.Get_DB_Connection()
        cursor = conn.cursor()
        
        query = """
        SELECT sender, message, send_at 
        FROM Chat_Messages 
        WHERE session_id = ? 
        ORDER BY send_at ASC
        """
        
        cursor.execute(query, (session_id,))
        messages = cursor.fetchall()
        conn.close()

        return messages
    
    def Delete_Session(self,session_id):
        conn = self.Get_DB_Connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM Chat_Messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM Chat_Sessions WHERE id = ?", (session_id,))
        
        conn.commit()  
        conn.close()  