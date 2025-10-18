# 1. достаём контент слайда
# 2. делаем оценку текста
# 3. делаем оценку релевантности картинок
# 4. отправляем на переделку
# 5. (после цикла) возвращаем финальный слайд

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase


class SlideEvaluationModel:

    metrics_list = {
        'Релевантность':
            [
                'Оцени, насколько ответ соответвует инструкциям из запроса'
            ],
        'Наличие галлюцинаций':
            [
                'Определи, содержит ли ответ ложную информацию',
                'Оцени, насколько ответ соответствует запросу по смыслу',
                'Понизь оценку, если в ответе опускаются важные детали'
            ],
        'Понятность':
            [
                'Оцени, насколько используемый язык понятный',
                'Проверь, используются ли сложные, нераспространённые слова (например, термины, жаргон, книжные слова)',
                'Если используются сложные слова, проверь, поясняются ли их значения',
                'Оцени, насколько понятно и подробно объясняются сложные идеи',
                'Определи любые расплывчатые или запутывающие детали, которые затрудняют понимание'
            ],
        'Правильность':
            [
                'Оцени, насколько представленный текст корректен с точки зрения правил русского языка',
                'Понизь оценку, если встречаются грамматические, орфографические и пунктуационные ошибки',
                'Оцени, насколько используемый язык соответствует тональности текста',
            ]
    }

    def evaluate_text(self, prompt, slide_text_content):
        metrics_values = []

        for metric, geval_prompt in self.metrics_list:
            curr_test_case = LLMTestCase(
                input=prompt,
                actual_output=slide_text_content
            )
            curr_metric = GEval(
                name=metric,
                evaluation_steps=geval_prompt,
                evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT]
            )

            curr_metric_value = curr_metric.measure(curr_test_case)
            metrics_values.append(curr_metric_value)

        return sum(metrics_values) / len(metrics_values)

    def evaluate_images(self, slide_image_content):
        pass
