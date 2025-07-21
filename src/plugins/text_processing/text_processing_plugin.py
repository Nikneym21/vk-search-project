import re
from typing import List, Dict, Any
from src.plugins.base_plugin import BasePlugin


class TextProcessingPlugin(BasePlugin):
    """Плагин для обработки текста"""
    
    def __init__(self):
        super().__init__("TextProcessingPlugin", "1.0.0")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация плагина"""
        try:
            self.logger.info("Инициализация TextProcessingPlugin")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {str(e)}")
            return False
    
    def clean_text_completely(self, text: str) -> str:
        """Полностью очищает текст от кодов эмодзи, хэштегов и лишних символов"""
        try:
            import emoji
            # Сначала удаляем эмодзи
            cleaned_text = emoji.demojize(text)
        except ImportError:
            cleaned_text = text
        
        # Удаляем коды эмодзи в формате :code:
        cleaned_text = re.sub(r':[a-zA-Z_]+:', '', cleaned_text)
        
        # Удаляем хэштеги (#слово)
        cleaned_text = re.sub(r'#\w+', '', cleaned_text)
        
        # Удаляем множественные пробелы
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Удаляем пробелы в начале и конце
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def clean_emojis_from_text(self, text: str) -> str:
        """Очищает эмодзи, коды эмодзи и хэштеги из текста"""
        return self.clean_text_completely(text)
    
    def clean_multiple_texts(self, texts: List[str]) -> List[str]:
        """Очищает список текстов от эмодзи, кодов эмодзи и хэштегов"""
        cleaned_texts = []
        for text in texts:
            cleaned_text = self.clean_text_completely(text)
            if cleaned_text:  # Проверяем, что после очистки текст не пустой
                cleaned_texts.append(cleaned_text)
        return cleaned_texts
    
    def extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста"""
        # Удаляем пунктуацию и приводим к нижнему регистру
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Разбиваем на слова
        words = text.split()
        
        # Удаляем стоп-слова (можно расширить список)
        stop_words = {'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между'}
        
        # Фильтруем слова длиной больше 2 символов и не являющиеся стоп-словами
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def find_duplicates(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Находит дубликаты в списке текстов"""
        duplicates = []
        seen = {}
        
        for i, text in enumerate(texts):
            cleaned_text = self.clean_text_completely(text)
            if cleaned_text in seen:
                duplicates.append({
                    'original_index': seen[cleaned_text],
                    'duplicate_index': i,
                    'text': cleaned_text
                })
            else:
                seen[cleaned_text] = i
        
        return duplicates
    
    def normalize_text(self, text: str) -> str:
        """Нормализует текст (приводит к единому формату)"""
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Заменяем множественные пробелы на один
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем пробелы в начале и конце
        text = text.strip()
        
        return text
    
    def split_text_into_chunks(self, text: str, max_length: int = 1000) -> List[str]:
        """Разбивает длинный текст на части"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Разбиваем по предложениям
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Если добавление предложения превысит лимит
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Если предложение само по себе длинное, разбиваем по словам
                    words = sentence.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                chunks.append(word)
                        else:
                            current_chunk += " " + word if current_chunk else word
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def remove_special_characters(self, text: str, keep_spaces: bool = True) -> str:
        """Удаляет специальные символы из текста"""
        if keep_spaces:
            # Оставляем буквы, цифры и пробелы
            return re.sub(r'[^\w\s]', '', text)
        else:
            # Оставляем только буквы и цифры
            return re.sub(r'[^\w]', '', text)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Выполняет основную логику плагина"""
        try:
            operation = kwargs.get('operation')
            text = kwargs.get('text', '')
            texts = kwargs.get('texts', [])
            
            if operation == 'clean_text':
                result = self.clean_text_completely(text)
                return {
                    'success': True,
                    'result': result
                }
            
            elif operation == 'clean_multiple':
                result = self.clean_multiple_texts(texts)
                return {
                    'success': True,
                    'result': result,
                    'count': len(result)
                }
            
            elif operation == 'extract_keywords':
                result = self.extract_keywords(text)
                return {
                    'success': True,
                    'result': result,
                    'count': len(result)
                }
            
            elif operation == 'find_duplicates':
                result = self.find_duplicates(texts)
                return {
                    'success': True,
                    'result': result,
                    'count': len(result)
                }
            
            elif operation == 'normalize':
                result = self.normalize_text(text)
                return {
                    'success': True,
                    'result': result
                }
            
            elif operation == 'split_chunks':
                max_length = kwargs.get('max_length', 1000)
                result = self.split_text_into_chunks(text, max_length)
                return {
                    'success': True,
                    'result': result,
                    'count': len(result)
                }
            
            elif operation == 'remove_special_chars':
                keep_spaces = kwargs.get('keep_spaces', True)
                result = self.remove_special_characters(text, keep_spaces)
                return {
                    'success': True,
                    'result': result
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Неизвестная операция: {operation}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup(self):
        """Очищает ресурсы"""
        pass 