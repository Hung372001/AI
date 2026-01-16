# Sample API Requests & Responses (JSON)

Below are example payloads for the planned tutoring API. Fields marked as `optional` can be omitted.

## Auth

### Register
**POST** `/api/auth/register`

**Request**
```json
{
  "email": "student@example.com",
  "name": "Nguyen Van A",
  "password": "strong-password"
}
```

**Response**
```json
{
  "id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "email": "student@example.com",
  "name": "Nguyen Van A",
  "role": "student",
  "created_at": "2025-01-01T10:00:00Z"
}
```

### Login
**POST** `/api/auth/login`

**Request**
```json
{
  "email": "student@example.com",
  "password": "strong-password"
}
```

**Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Documents

### Upload document
**POST** `/api/admin/documents`

**Response**
```json
{
  "id": "4c3ff54c-56f1-4bc9-97df-23b3b0fdc324",
  "title": "sach-toan-10.pdf",
  "doc_type": "pdf",
  "source": null,
  "file_path": "uploads/4c3ff54c-56f1-4bc9-97df-23b3b0fdc324_sach-toan-10.pdf",
  "grade": 10,
  "topic": "hinh-hoc",
  "uploaded_at": "2025-01-01T10:05:00Z"
}
```

### Process document
**POST** `/api/admin/documents/{document_id}/process`

**Response**
```json
{
  "status": "processed"
}
```

---

## Tutor Chat

### Send message
**POST** `/api/tutor/chat`

**Request**
```json
{
  "user_id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "session_id": "c3a7a4f4-7b1c-4a1b-9c9e-25d2c6e3c2a1",
  "message": "Giải thích định lý Pitago giúp em.",
  "topic": "hinh-hoc",
  "grade": 10
}
```

**Response**
```json
{
  "reply": "Định lý Pitago nói rằng trong tam giác vuông, bình phương cạnh huyền bằng tổng bình phương hai cạnh góc vuông...",
  "context": [
    {
      "chunk_id": "a1f07d66-7b6e-4d75-8c1d-5a5db5035a0f",
      "content": "Định lý Pitago: c^2 = a^2 + b^2",
      "score": 0.89
    }
  ],
  "suggested_questions": [
    "Em có thể áp dụng định lý Pitago vào bài nào?",
    "Em thử tính cạnh huyền khi biết hai cạnh góc vuông nhé?"
  ]
}
```

### List sessions
**GET** `/api/tutor/sessions?user_id={user_id}`

**Response**
```json
{
  "sessions": [
    {
      "id": "c3a7a4f4-7b1c-4a1b-9c9e-25d2c6e3c2a1",
      "topic": "hinh-hoc",
      "created_at": "2025-01-01T10:10:00Z"
    }
  ]
}
```

### Get messages in a session
**GET** `/api/tutor/sessions/{session_id}/messages`

**Response**
```json
{
  "messages": [
    {
      "id": "4a8f2b54-2b7a-42be-90cc-2b7e9c2c91f5",
      "role": "user",
      "content": "Giải thích định lý Pitago giúp em.",
      "created_at": "2025-01-01T10:10:00Z"
    },
    {
      "id": "5b11c2a6-4e35-4c66-9fb0-79ad9e4c49ff",
      "role": "assistant",
      "content": "Định lý Pitago nói rằng...",
      "created_at": "2025-01-01T10:10:01Z"
    }
  ]
}
```

---

## Learning Mastery

### Get mastery
**GET** `/api/progress?user_id={user_id}`

**Response**
```json
{
  "user_id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "topics": [
    {
      "topic": "hinh-hoc",
      "mastery_score": 0.62,
      "last_updated": "2025-01-01T10:12:00Z"
    }
  ],
  "topics_weak": [
    "hinh-hoc"
  ]
}
```

---

## Assignments

### Create assignment
**POST** `/api/assignments`

**Request**
```json
{
  "user_id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "topic": "hinh-hoc",
  "difficulty": 2
}
```

**Response**
```json
{
  "id": "f7e9f5c3-2dc8-47c0-8a9c-4bde3b7db08d",
  "user_id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "topic": "hinh-hoc",
  "difficulty": 2,
  "created_at": "2025-01-01T10:15:00Z",
  "questions": [
    {
      "id": "c0c8f3c8-00a1-46aa-8443-651ddf1abf1d",
      "question_text": "Trong tam giác vuông có hai cạnh góc vuông là 3 và 4, cạnh huyền là bao nhiêu?",
      "hint": "Áp dụng định lý Pitago."
    }
  ]
}
```

### Submit attempt
**POST** `/api/assignments/{assignment_id}/submit`

**Request**
```json
{
  "user_id": "f502f3f1-4a2e-46a5-8e5e-0d9a7a2b9b2c",
  "attempts": [
    {
      "question_id": "c0c8f3c8-00a1-46aa-8443-651ddf1abf1d",
      "student_answer": "5"
    }
  ]
}
```

**Response**
```json
{
  "assignment_id": "f7e9f5c3-2dc8-47c0-8a9c-4bde3b7db08d",
  "summary": {
    "score": 1.0,
    "correct": 1,
    "total": 1
  },
  "attempts": [
    {
      "question_id": "c0c8f3c8-00a1-46aa-8443-651ddf1abf1d",
      "score": 1.0,
      "feedback": "Đúng rồi! 3-4-5 là tam giác vuông."
    }
  ]
}
```
