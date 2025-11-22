"""Flask web application for QuizForge."""

from __future__ import annotations

import io
import os
import zipfile
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.exceptions import BadRequest

from ..services.packager import Packager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size

packager = Packager()


@app.route('/')
def index():
    """Serve the main quiz editor page."""
    return render_template('index.html')


@app.route('/modules')
def modules():
    """Serve the modules download page."""
    return render_template('modules.html')


@app.route('/modules/download/<filename>')
def download_module(filename):
    """Serve module files for download."""
    # Security: only allow .md files and prevent directory traversal
    if not filename.endswith('.md'):
        return "Invalid file type", 400
    
    if '..' in filename or '/' in filename or '\\' in filename:
        return "Invalid filename", 400
    
    # Determine the module path
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Check if it's the base module
    if filename == 'QF_BASE.md':
        file_path = os.path.join(base_path, filename)
    # Check for discipline modules
    elif filename.startswith('QF_MOD_'):
        discipline = filename.replace('QF_MOD_', '').replace('.md', '')
        if discipline in ['CompSci', 'ELA', 'Humanities', 'Math', 'Science']:
            file_path = os.path.join(base_path, 'QF_MODULES', 'Disciplines', filename)
        elif discipline in ['Differentiation', 'Rigor', 'UDL']:
            file_path = os.path.join(base_path, 'QF_MODULES', 'Pedagogy', filename)
        else:
            return "Module not found", 404
    else:
        return "Module not found", 404
    
    # Verify file exists
    if not os.path.exists(file_path):
        return f"Module not found: {filename}", 404
    
    # Send the file
    return send_file(file_path, as_attachment=True, download_name=filename)


@app.route('/modules/download-bundle', methods=['POST'])
def download_bundle():
    """Create and download a ZIP of selected modules."""
    try:
        data = request.get_json()
        if not data or 'modules' not in data:
            return jsonify({'error': 'Missing modules list'}), 400
        
        modules = data['modules']
        if not modules or not isinstance(modules, list):
            return jsonify({'error': 'Invalid modules list'}), 400
        
        # Ensure QF_BASE.md is always included
        if 'QF_BASE.md' not in modules:
            modules.insert(0, 'QF_BASE.md')
        
        # Create ZIP in memory
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename in modules:
                # Security check
                if not filename.endswith('.md') or '..' in filename or '/' in filename or '\\' in filename:
                    continue
                
                # Determine file path
                if filename == 'QF_BASE.md':
                    file_path = os.path.join(base_path, filename)
                elif filename.startswith('QF_MOD_'):
                    discipline = filename.replace('QF_MOD_', '').replace('.md', '')
                    if discipline in ['CompSci', 'ELA', 'Humanities', 'Math', 'Science']:
                        file_path = os.path.join(base_path, 'QF_MODULES', 'Disciplines', filename)
                    elif discipline in ['Differentiation', 'Rigor', 'UDL']:
                        file_path = os.path.join(base_path, 'QF_MODULES', 'Pedagogy', filename)
                    else:
                        continue
                else:
                    continue
                
                # Add file to ZIP if it exists
                if os.path.exists(file_path):
                    zip_file.write(file_path, filename)
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='QuizForge_Modules.zip'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate quiz text without generating a package."""
    try:
        data = request.get_json()
        if not data or 'quiz_text' not in data:
            return jsonify({'error': 'Missing quiz_text'}), 400
        
        quiz_text = data['quiz_text']
        title = data.get('title')
        
        if not quiz_text.strip():
            return jsonify({'error': 'Quiz text cannot be empty'}), 400
        
        # Validate and get summary
        summary = packager.summarize_text(quiz_text, title_override=title)
        
        return jsonify({
            'valid': True,
            'summary': summary
        })
    
    except ValueError as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate QTI package from quiz text."""
    try:
        data = request.get_json()
        if not data or 'quiz_text' not in data:
            return jsonify({'error': 'Missing quiz_text'}), 400
        
        quiz_text = data['quiz_text']
        title = data.get('title')
        
        if not quiz_text.strip():
            return jsonify({'error': 'Quiz text cannot be empty'}), 400
        
        # Generate package
        package = packager.package_text(quiz_text, title_override=title)

        # Send as downloadable file
        filename = f"{package.quiz.title.replace(' ', '_')}.zip"
        response = send_file(
            io.BytesIO(package.zip_bytes),
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        response.headers['X-QuizForge-Items'] = str(package.inspection.item_count)
        if package.inspection.question_type_counts:
            summary = '; '.join(
                f"{qtype}:{count}"
                for qtype, count in sorted(package.inspection.question_type_counts.items())
            )
            response.headers['X-QuizForge-Question-Types'] = summary
        return response
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'QuizForge'})


if __name__ == '__main__':
    app.run(debug=True)
