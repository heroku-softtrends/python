# Frontend Update Guide for AI-Powered Invoice Reader

## 🎯 Overview
Your backend has been upgraded from regex-based processing to AI-powered extraction using BERT and DistilBERT models. This guide shows you how to update your React frontend to take advantage of the new AI capabilities.

## 📋 Required Updates

### 1. Update API Configuration

**File: `src/api/config.js` or `src/config/api.js`**
```javascript
// Ensure your API base URL points to the backend
export const API_BASE_URL = 'http://localhost:8000/api';

// Add timeout for AI processing (may take longer)
export const API_TIMEOUT = 60000; // 60 seconds for AI processing
```

### 2. Enhanced Upload Service

**File: `src/services/uploadService.js` (or similar)**
```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Configure axios with longer timeout for AI processing
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for AI processing
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});

export const uploadInvoice = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await apiClient.post('/upload', formData, {
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress?.(percentCompleted);
      }
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Upload failed');
    }
    throw new Error('Network error - please check if backend is running');
  }
};

// NEW: Get AI model status
export const getAIModelStatus = async () => {
  try {
    const response = await apiClient.get('/ai/models');
    return response.data;
  } catch (error) {
    console.error('Failed to get AI model status:', error);
    return null;
  }
};

// NEW: Submit feedback for AI learning
export const submitAIFeedback = async (invoiceId, corrections) => {
  try {
    const response = await apiClient.post('/train/feedback', {
      invoice_id: invoiceId,
      field_corrections: corrections
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to submit feedback');
  }
};
```

### 3. Enhanced Field Display Component

**Create or update: `src/components/ExtractedFields.jsx`**
```jsx
import React, { useState } from 'react';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Chip,
  TextField,
  Box,
  Typography,
  Tooltip,
  IconButton
} from '@mui/material';
import { Edit, Check, Close } from '@mui/icons-material';

const ExtractedFields = ({ fields, onFieldChange, onFieldCorrection }) => {
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');

  const getConfidenceColor = (score) => {
    if (score > 0.8) return 'success';
    if (score > 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (score) => {
    const percentage = (score * 100).toFixed(1);
    if (score > 0.8) return `${percentage}% (High)`;
    if (score > 0.6) return `${percentage}% (Medium)`;
    return `${percentage}% (Low)`;
  };

  const handleEdit = (field) => {
    setEditingField(field.field_name);
    setEditValue(field.field_value);
  };

  const handleSaveEdit = (fieldName) => {
    onFieldCorrection?.(fieldName, editValue);
    setEditingField(null);
  };

  const handleCancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        🤖 AI-Extracted Fields
      </Typography>
      
      <List>
        {fields.map((field, index) => (
          <ListItem key={index} divider>
            <ListItemIcon>
              <Checkbox
                checked={field.is_selected}
                onChange={(e) => onFieldChange(field.field_name, e.target.checked)}
              />
            </ListItemIcon>
            
            <ListItemText
              primary={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="subtitle2">
                    {field.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Typography>
                  <Tooltip title={`AI Confidence: ${getConfidenceLabel(field.confidence_score)}`}>
                    <Chip
                      label={`${(field.confidence_score * 100).toFixed(1)}%`}
                      color={getConfidenceColor(field.confidence_score)}
                      size="small"
                    />
                  </Tooltip>
                </Box>
              }
              secondary={
                editingField === field.field_name ? (
                  <Box display="flex" alignItems="center" gap={1} mt={1}>
                    <TextField
                      size="small"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit(field.field_name)}
                    />
                    <IconButton size="small" onClick={() => handleSaveEdit(field.field_name)}>
                      <Check />
                    </IconButton>
                    <IconButton size="small" onClick={handleCancelEdit}>
                      <Close />
                    </IconButton>
                  </Box>
                ) : (
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2">{field.field_value}</Typography>
                    <IconButton size="small" onClick={() => handleEdit(field)}>
                      <Edit />
                    </IconButton>
                  </Box>
                )
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default ExtractedFields;
```

### 4. AI Status Component

**Create: `src/components/AIStatus.jsx`**
```jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import { SmartToy } from '@mui/icons-material';
import { getAIModelStatus } from '../services/uploadService';

const AIStatus = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAIStatus = async () => {
      try {
        const status = await getAIModelStatus();
        setAiStatus(status);
      } catch (err) {
        setError('Failed to load AI status');
      } finally {
        setLoading(false);
      }
    };

    fetchAIStatus();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={1}>
            <CircularProgress size={20} />
            <Typography>Loading AI status...</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert severity="warning">{error}</Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <SmartToy />
          <Typography variant="h6">AI Models Active</Typography>
        </Box>
        
        {aiStatus?.models_used?.map((model, index) => (
          <Chip
            key={index}
            label={model}
            color="primary"
            style={{ margin: 2 }}
            size="small"
          />
        ))}
        
        <Typography variant="body2" color="textSecondary" mt={1}>
          Processing: {aiStatus?.processing_methods?.join(', ')}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Device: {aiStatus?.device || 'CPU'}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default AIStatus;
```

### 5. Enhanced Upload Component

**Update your main upload component:**
```jsx
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Snackbar
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { uploadInvoice } from '../services/uploadService';
import ExtractedFields from './ExtractedFields';
import AIStatus from './AIStatus';

const UploadComponent = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const response = await uploadInvoice(selectedFile, setProgress);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleFieldChange = (fieldName, selected) => {
    if (result) {
      const updatedFields = result.extracted_fields.map(field =>
        field.field_name === fieldName 
          ? { ...field, is_selected: selected }
          : field
      );
      setResult({ ...result, extracted_fields: updatedFields });
    }
  };

  const handleFieldCorrection = (fieldName, newValue) => {
    // Update the field value and mark for feedback
    if (result) {
      const updatedFields = result.extracted_fields.map(field =>
        field.field_name === fieldName 
          ? { ...field, field_value: newValue, user_corrected: true }
          : field
      );
      setResult({ ...result, extracted_fields: updatedFields });
    }
  };

  return (
    <Box p={3}>
      {/* AI Status */}
      <AIStatus />
      
      {/* Upload Section */}
      <Paper elevation={3} style={{ padding: 20, marginTop: 20 }}>
        <Typography variant="h5" gutterBottom>
          📄 Upload Invoice for AI Processing
        </Typography>
        
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          style={{ marginBottom: 16 }}
        />
        
        {selectedFile && (
          <Typography variant="body2" gutterBottom>
            Selected: {selectedFile.name}
          </Typography>
        )}
        
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          startIcon={<CloudUpload />}
        >
          {uploading ? 'Processing with AI...' : 'Upload & Process'}
        </Button>
        
        {uploading && (
          <Box mt={2}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="body2" color="textSecondary" align="center">
              AI is analyzing your document... {progress}%
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Results */}
      {result && (
        <Paper elevation={3} style={{ padding: 20, marginTop: 20 }}>
          <ExtractedFields
            fields={result.extracted_fields}
            onFieldChange={handleFieldChange}
            onFieldCorrection={handleFieldCorrection}
          />
        </Paper>
      )}

      {/* Error Handling */}
      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default UploadComponent;
```

### 6. Package.json Dependencies

**Ensure you have these dependencies:**
```json
{
  "dependencies": {
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0"
  }
}
```

## 🚀 Implementation Steps

1. **Update API configuration** with longer timeouts
2. **Replace or enhance your upload service** with AI-aware methods  
3. **Update field display components** to show confidence scores
4. **Add AI status component** to show active models
5. **Enhance error handling** for AI processing timeouts
6. **Test with your backend** running on port 8000

## ✨ New Features You Get

- **Visual confidence indicators** (green/yellow/red chips)
- **Real-time AI model status** 
- **Inline field editing** with correction feedback
- **Better error handling** for AI processing
- **Longer timeout support** for complex documents
- **Professional UI** with Material-UI components

Your frontend will now display the superior accuracy and intelligence of the AI-powered backend! 🤖✨