#!/usr/bin/env python3
"""
YAML document filtering utility
Extracts valid YAML documents from AI model responses
"""

import yaml
import logging
import re
from typing import Optional


def clean_yaml_aliases(text: str) -> str:
    """
    Remove invalid YAML aliases that cause parsing errors
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text with aliases removed
    """
    # Remove lines starting with * (YAML aliases and bullet points)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that start with * followed by space or ** (invalid aliases/markdown)
        if re.match(r'^\s*\*+\s+', line):
            continue
        # Skip lines that contain only * (invalid aliases)
        if re.match(r'^\s*\*+\s*$', line):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def filter_yaml_document(response: str, priority_keys: Optional[list] = None) -> str:
    """
    Extracts a valid single YAML document from the response
    
    Args:
        response: AIモデルからの応答テキスト
        priority_keys: 優先的に検索するキーのリスト（デフォルト: ['wave_config', 'version', 'project']）
        
    Returns:
        フィルタリングされた単一YAMLドキュメント
    """
    if priority_keys is None:
        priority_keys = ['wave_config', 'version', 'project']
    
    logger = logging.getLogger(__name__)
    
    try:
        # Clean YAML aliases first
        cleaned_response = clean_yaml_aliases(response)
        
        # Split multiple documents
        documents = cleaned_response.split('---')
        
        # Search for YAML documents containing priority keys
        for doc in documents:
            doc = doc.strip()
            if not doc:
                continue
                
            try:
                # Try parsing as YAML
                parsed = yaml.safe_load(doc)
                # Prioritize YAML containing priority keys
                if isinstance(parsed, dict) and any(key in str(parsed) for key in priority_keys):
                    logger.debug(f"Found YAML document with priority keys: {priority_keys}")
                    return doc
            except yaml.YAMLError:
                continue
        
        # 優先キーが見つからない場合は最初の有効なYAMLを返す
        for doc in documents:
            doc = doc.strip()
            if not doc:
                continue
                
            try:
                yaml.safe_load(doc)
                logger.debug("最初の有効なYAMLドキュメントを返します")
                return doc
            except yaml.YAMLError:
                continue
                
        # 有効なYAMLが見つからない場合は元の応答を返す
        logger.debug("有効なYAMLドキュメントが見つかりませんでした。元の応答を返します")
        return response
        
    except Exception as e:
        logger.debug(f"YAMLフィルタリングエラー: {str(e)}")
        return response


def is_valid_yaml(text: str) -> bool:
    """
    テキストが有効なYAMLであるかをチェック
    
    Args:
        text: チェックするテキスト
        
    Returns:
        有効なYAMLの場合はTrue
    """
    try:
        yaml.safe_load(text)
        return True
    except yaml.YAMLError:
        return False


def extract_yaml_blocks(text: str) -> list:
    """
    テキストからYAMLブロックを抽出
    
    Args:
        text: 抽出元のテキスト
        
    Returns:
        YAMLブロックのリスト
    """
    documents = text.split('---')
    yaml_blocks = []
    
    for doc in documents:
        doc = doc.strip()
        if doc and is_valid_yaml(doc):
            yaml_blocks.append(doc)
    
    return yaml_blocks
