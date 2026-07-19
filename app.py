import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple
import gradio as gr

class TreeParser:
    """Parses visual ASCII/Markdown trees into hierarchical Path objects."""
    KNOWN_FILES = {
        '.gitignore', '.env', '.dockerignore', 'Dockerfile', 'LICENSE', 
        'Makefile', 'README', 'setup.py', '.prettierrc', '.eslintrc'
    }

    def parse(self, text: str) -> Tuple[List[Tuple[Path, bool]], List[str]]:
        parsed_nodes: List[Tuple[Path, bool]] = []
        stack: List[Tuple[int, Path]] = []
        roots: List[str] = []

        lines = text.splitlines()
        for line in lines:
            line = line.rstrip('\r\n')
            if not line or "```" in line:
                continue

            normalized_line = line.replace('\t', '    ')
            match = re.match(r'^([│├└|\\+\s]*[─\-]*\s*)(.*)$', normalized_line)
            if not match:
                continue

            prefix, name = match.groups()
            name = name.strip()
            if not name:
                continue

            depth = len(prefix)
            name = name.replace('\\', '/')
            
            is_dir = False
            if name.endswith('/'):
                is_dir = True
                name = name[:-1]

            name = name.strip('/')
            name = re.sub(r'[<>:"|?*]', '', name)

            if not name:
                continue

            if not is_dir:
                if name in self.KNOWN_FILES or "." in name.lstrip("."):
                    is_dir = False
                else:
                    is_dir = True

            while stack and stack[-1][0] >= depth:
                stack.pop()

            if stack:
                parent_path = stack[-1][1]
                current_path = parent_path / name
            else:
                current_path = Path(name)
                root_name = current_path.parts[0]
                if root_name not in roots:
                    roots.append(root_name)

            parsed_nodes.append((current_path, is_dir))

            if is_dir:
                stack.append((depth, current_path))

        return parsed_nodes, roots

def generate_structure(tree_text: str):
    if not tree_text or not tree_text.strip():
        return "အမှားပြနေပါသည်: Project Tree စာသားထည့်ပေးပါ။", None
        
    parser = TreeParser()
    paths, roots = parser.parse(tree_text)
    
    if not paths:
        return "အမှားပြနေပါသည်: ပုံစံမှန်ကန်သော Tree Structure မဟုတ်ပါ။", None

    temp_dir = Path(tempfile.mkdtemp())
    
    created_folders = 0
    created_files = 0
    
    for path, is_dir in paths:
        full_path = temp_dir / path
        if is_dir:
            full_path.mkdir(parents=True, exist_ok=True)
            created_folders += 1
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            created_files += 1

    zip_filename = f"{roots[0]}.zip" if roots else "project_structure.zip"
    zip_path = temp_dir / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root in roots:
            root_path = temp_dir / root
            if root_path.exists():
                zf.write(root_path, root_path.relative_to(temp_dir))
                if root_path.is_dir():
                    for file_path in root_path.rglob('*'):
                        zf.write(file_path, file_path.relative_to(temp_dir))
                        
    success_msg = f"✅ အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!\n\nFolders အရေအတွက်: {created_folders}\nFiles အရေအတွက်: {created_files}\nအောက်ပါ ZIP ဖိုင်ကို Download ရယူနိုင်ပါသည်။"
    
    return success_msg, str(zip_path)

# --- Define Gradio UI (Theme ရွှေ့ထားပါသည်) ---
with gr.Blocks(title="Structure Generator Tool") as demo:
    gr.Markdown("# 📂 Project Structure Generator")
    gr.Markdown("ASCII/Markdown Tree စာသားများကို အမှန်တကယ် File/Folder များအဖြစ် ပြောင်းလဲပေးမည့် Tool ဖြစ်ပါသည်။")
    
    with gr.Row():
        with gr.Column(scale=2):
            tree_input = gr.Textbox(
                lines=15, 
                placeholder="ဒီနေရာမှာ သင့်ရဲ့ Project Tree ကို Paste ချပါ...", 
                label="Input Tree Structure"
            )
            generate_btn = gr.Button("🚀 File များတည်ဆောက်ရန် (Generate & Zip)", variant="primary")
            
        with gr.Column(scale=1):
            output_msg = gr.Textbox(label="Status / မှတ်တမ်း", interactive=False, lines=5)
            output_file = gr.File(label="Download ZIP File")
            
    generate_btn.click(
        fn=generate_structure,
        inputs=[tree_input],
        outputs=[output_msg, output_file]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
  
