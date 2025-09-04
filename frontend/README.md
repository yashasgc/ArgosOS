# ArgosOS Frontend

A modern React-based frontend for the ArgosOS document management system, built with Vite, TypeScript, Tailwind CSS, and ShadCN UI components.

## 🚀 Features

- **File Upload**: Drag & drop file upload with progress tracking
- **Document Management**: View, organize, and manage uploaded documents
- **AI-Powered Search**: Natural language search across all documents
- **Responsive Design**: Mobile-first design with sidebar navigation
- **Settings Management**: Configure API endpoints and OpenAI keys
- **Modern UI**: Clean, intuitive interface built with Tailwind CSS

## 🛠️ Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: ShadCN UI + Lucide React icons
- **State Management**: Zustand
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Package Manager**: npm

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── FileCard.tsx     # Document display card
│   ├── FileUpload.tsx   # File upload component
│   ├── SearchResultCard.tsx # Search result display
│   └── Sidebar.tsx      # Navigation sidebar
├── pages/               # Page components
│   ├── Home.tsx         # Landing page with upload
│   ├── Documents.tsx    # Document management
│   ├── Search.tsx       # AI-powered search
│   └── Settings.tsx     # Configuration settings
├── store/               # State management
│   └── useConfigStore.ts # Configuration store
├── lib/                 # Utility libraries
│   ├── api.ts          # API client wrapper
│   └── utils.ts        # Utility functions
└── App.tsx             # Main app component
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- ArgosOS backend running (default: http://localhost:8000)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ArgosOS/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## 🔧 Configuration

### API Configuration

1. Go to **Settings** page
2. Set your **API Base URL** (default: http://localhost:8000)
3. Test the connection
4. Save your settings

### OpenAI Integration (Optional)

1. In **Settings**, add your OpenAI API key
2. Enable AI-powered search features
3. Your key is stored locally and never sent to our servers

## 📱 Usage

### Home Page
- **Upload Files**: Drag & drop or click to browse
- **Supported Formats**: PDF, TXT, DOC, DOCX, MD, RTF
- **Recent Uploads**: View recently processed documents

### Documents Page
- **Browse**: View all uploaded documents
- **Search**: Filter by content or tags
- **View Modes**: Grid or list layout
- **Tags**: Organize documents with tags

### Search Page
- **Natural Language**: Ask questions in plain English
- **Content Search**: Find documents by keywords
- **AI-Powered**: Get intelligent search results
- **Highlighted Results**: See matching content snippets

### Settings Page
- **API Configuration**: Set backend URL and test connection
- **OpenAI Setup**: Configure AI features
- **Persistent Storage**: Settings saved to localStorage

## 🔌 API Integration

The frontend communicates with your ArgosOS backend through these endpoints:

- `GET /health` - Health check
- `POST /upload` - File upload
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get specific document
- `POST /search` - Search documents
- `GET /tags` - List all tags
- `POST /tags` - Create new tag

## 🎨 Customization

### Styling
- Modify `tailwind.config.js` for theme customization
- Update `src/index.css` for global styles
- Use Tailwind utility classes throughout components

### Components
- All components are built with ShadCN UI patterns
- Easy to customize with Tailwind classes
- Responsive design built-in

### State Management
- Zustand store for configuration
- Local state for component-specific data
- Easy to extend with additional stores

## 🧪 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

### Code Style

- TypeScript for type safety
- Functional components with hooks
- Consistent naming conventions
- Component-based architecture

## 🚀 Deployment

### Static Hosting
The built frontend can be deployed to any static hosting service:

- **Vercel**: Connect your GitHub repository
- **Netlify**: Drag & drop the `dist/` folder
- **GitHub Pages**: Enable in repository settings
- **AWS S3**: Upload `dist/` contents

### Environment Variables
For production, you may want to set:

```bash
VITE_API_BASE_URL=https://your-api-domain.com
VITE_APP_TITLE=ArgosOS
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of ArgosOS and follows the same license terms.

## 🆘 Support

- Check the [Issues](../../issues) page for known problems
- Create a new issue for bugs or feature requests
- Review the backend documentation for API details

---

**Built with ❤️ for the ArgosOS project**
