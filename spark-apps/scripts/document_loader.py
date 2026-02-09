"""
Enterprise Document Loader
- PDF, TXT, MD support
- Metadata extraction
- Smart chunking
- Error handling
"""
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import hashlib
import PyPDF2
import markdown
from dataclasses import dataclass

@dataclass
class Document:
    """Document metadata structure"""
    doc_id: str
    filename: str
    content: str
    file_type: str
    file_size: int
    created_at: datetime
    metadata: Dict[str, str]

class DocumentLoader:
    """Production-grade document loader"""
    
    def __init__(self, data_dir: str = "../../data/documents"):
        self.data_dir = Path(data_dir)
        self.supported_types = {'.txt', '.md', '.pdf'}
    
    def load_all(self) -> List[Document]:
        """Load all documents from directory"""
        documents = []
        
        if not self.data_dir.exists():
            print(f"⚠️  Directory {self.data_dir} not found!")
            return documents
        
        for file_path in self.data_dir.rglob('*'):
            if file_path.suffix.lower() in self.supported_types:
                try:
                    doc = self.load_document(file_path)
                    documents.append(doc)
                    print(f"✅ Loaded: {file_path.name}")
                except Exception as e:
                    print(f"❌ Error loading {file_path.name}: {e}")
        
        return documents
    
    def load_document(self, file_path: Path) -> Document:
        """Load single document"""
        # Read content
        content = self._read_file(file_path)
        
        # Generate doc_id
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()[:16]
        
        # Extract metadata
        stat = file_path.stat()
        
        return Document(
            doc_id=doc_id,
            filename=file_path.name,
            content=content,
            file_type=file_path.suffix[1:],  # Remove dot
            file_size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime),
            metadata={
                'path': str(file_path),
                'extension': file_path.suffix
            }
        )
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content based on type"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.txt':
            return self._read_txt(file_path)
        elif suffix == '.md':
            return self._read_md(file_path)
        elif suffix == '.pdf':
            return self._read_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def _read_txt(self, file_path: Path) -> str:
        """Read TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_md(self, file_path: Path) -> str:
        """Read Markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            # Convert to plain text (remove markdown syntax)
            html = markdown.markdown(md_content)
            # Simple HTML tag removal
            import re
            text = re.sub('<[^<]+?>', '', html)
            return text
    
    def _read_pdf(self, file_path: Path) -> str:
        """Read PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"PDF read error: {e}")
        return text


class SmartChunker:
    """Production-grade chunking with overlap"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, doc: Document) -> List[Dict]:
        """Chunk document into smaller pieces"""
        chunks = []
        text = doc.content
        
        # Split by sentences first (smarter chunking)
        sentences = self._split_sentences(text)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:  # Save current chunk
                    chunks.append(self._create_chunk(
                        doc, current_chunk, chunk_index
                    ))
                    chunk_index += 1
                    
                    # Keep overlap
                    words = current_chunk.split()
                    overlap_text = ' '.join(words[-self.overlap:])
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        # Add last chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                doc, current_chunk, chunk_index
            ))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunk(self, doc: Document, text: str, index: int) -> Dict:
        """Create chunk metadata"""
        chunk_id = hashlib.md5(f"{doc.doc_id}-{index}".encode()).hexdigest()[:16]
        
        return {
            'chunk_id': chunk_id,
            'doc_id': doc.doc_id,
            'chunk_index': index,
            'chunk_text': text.strip(),
            'chunk_size': len(text),
            'doc_filename': doc.filename,
            'doc_type': doc.file_type,
            'chunking_strategy': f'smart-{self.chunk_size}-overlap-{self.overlap}'
        }


# Test
if __name__ == "__main__":
    print("🚀 Enterprise Document Loader Test\n")
    print("=" * 60)
    
    # Load documents
    loader = DocumentLoader()
    documents = loader.load_all()
    
    print(f"\n📊 Loaded {len(documents)} documents\n")
    
    # Chunk documents
    chunker = SmartChunker(chunk_size=500, overlap=100)
    all_chunks = []
    
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"   📄 {doc.filename}: {len(chunks)} chunks")
    
    print(f"\n✅ Total chunks: {len(all_chunks)}")
    print("=" * 60)
