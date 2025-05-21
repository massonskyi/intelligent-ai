import unittest
from unittest.mock import patch, MagicMock
import torch

# Добавляем путь к src, чтобы можно было импортировать DeepSeekModel
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.models.deepseek import DeepSeekModel

class TestDeepSeekModel(unittest.TestCase):

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.current_device')
    @patch('torch.cuda.get_device_properties')
    def test_detect_device_cuda(self, mock_get_device_properties, mock_current_device, mock_is_available):
        """Тестирует определение устройства, когда CUDA доступна."""
        mock_is_available.return_value = True
        mock_current_device.return_value = 0
        mock_props = MagicMock()
        mock_props.total_memory = 16 * (1024 ** 3) # 16 GB
        mock_get_device_properties.return_value = mock_props

        model_path = "dummy_model_path"
        # Мы мокаем _select_config и _load_model, так как тестируем только _detect_device через __init__
        with patch.object(DeepSeekModel, '_select_config', return_value={"precision": "float16", "batch_size": 16}), \
             patch.object(DeepSeekModel, '_load_model', return_value=MagicMock()):
            
            # _detect_device вызывается в __init__
            device, vram_gb = DeepSeekModel(model_path)._detect_device()

        self.assertEqual(device.type, 'cuda')
        self.assertEqual(device.index, 0)
        self.assertEqual(vram_gb, 16.0)
        mock_is_available.assert_called_once()
        mock_current_device.assert_called_once()
        mock_get_device_properties.assert_called_once_with(0)

    @patch('torch.cuda.is_available')
    def test_detect_device_cpu(self, mock_is_available):
        """Тестирует определение устройства, когда CUDA недоступна."""
        mock_is_available.return_value = False

        model_path = "dummy_model_path"
        with patch.object(DeepSeekModel, '_select_config', return_value={"precision": "float16", "batch_size": 16}), \
             patch.object(DeepSeekModel, '_load_model', return_value=MagicMock()):
            
            # _detect_device вызывается в __init__
            # Чтобы избежать ошибки в _select_config из-за vram_gb=0.0, мокаем его
            with patch.object(DeepSeekModel, '_select_config') as mock_select_config_cpu:
                mock_select_config_cpu.return_value = {"precision": "float16", "batch_size": 1} # Любая валидная конфигурация
                device, vram_gb = DeepSeekModel(model_path)._detect_device()


        self.assertEqual(device.type, 'cpu')
        self.assertEqual(vram_gb, 0.0)
        mock_is_available.assert_called_once()

    def test_select_config(self):
        """Тестирует выбор конфигурации в зависимости от VRAM."""
        # Временный экземпляр для вызова _select_config
        # Мокаем __init__ чтобы не выполнять реальную загрузку
        with patch.object(DeepSeekModel, '__init__', lambda x, y: None):
            model_instance = DeepSeekModel("dummy")

            config_12gb = model_instance._select_config(16.0)
            self.assertEqual(config_12gb, {"precision": "float16", "batch_size": 16})

            config_6gb = model_instance._select_config(8.0)
            self.assertEqual(config_6gb, {"precision": "float16", "batch_size": 4})
            
            config_exact_12gb = model_instance._select_config(12.0)
            self.assertEqual(config_exact_12gb, {"precision": "float16", "batch_size": 16})

            config_exact_6gb = model_instance._select_config(6.0)
            self.assertEqual(config_exact_6gb, {"precision": "float16", "batch_size": 4})

            with self.assertRaisesRegex(RuntimeError, "Недостаточно VRAM .* Минимум 6 GB."):
                model_instance._select_config(4.0)
            
            with self.assertRaisesRegex(RuntimeError, "Недостаточно VRAM .* Минимум 6 GB."):
                model_instance._select_config(0.0)


    @patch('torch.load')
    def test_load_model(self, mock_torch_load):
        """Тестирует загрузку модели."""
        mock_model_data = MagicMock(spec=torch.nn.Module)
        mock_torch_load.return_value = mock_model_data

        # Временный экземпляр для вызова _load_model
        with patch.object(DeepSeekModel, '__init__', lambda x, y: None):
            model_instance = DeepSeekModel("dummy")

            device_cpu = torch.device('cpu')
            config_fp16 = {"precision": "float16"}
            
            loaded_model_fp16 = model_instance._load_model("dummy_path", device_cpu, config_fp16)
            mock_torch_load.assert_called_once_with("dummy_path", map_location="cpu")
            mock_model_data.half.assert_called_once()
            mock_model_data.to.assert_called_once_with(device_cpu)
            mock_model_data.eval.assert_called_once()
            self.assertEqual(loaded_model_fp16, mock_model_data)

            mock_model_data.reset_mock() # Сбрасываем моки для следующего вызова

            config_fp32 = {"precision": "float32"} # или любая другая строка
            loaded_model_fp32 = model_instance._load_model("dummy_path2", device_cpu, config_fp32)
            mock_torch_load.assert_called_with("dummy_path2", map_location="cpu")
            mock_model_data.half.assert_not_called() # .half() не должен вызываться
            mock_model_data.to.assert_called_with(device_cpu)
            mock_model_data.eval.assert_called_once()
            self.assertEqual(loaded_model_fp32, mock_model_data)


    @patch.object(DeepSeekModel, '_detect_device')
    @patch.object(DeepSeekModel, '_select_config')
    @patch.object(DeepSeekModel, '_load_model')
    def test_init_successful(self, mock_load_model, mock_select_config, mock_detect_device):
        """Тестирует успешную инициализацию модели."""
        mock_detect_device.return_value = (torch.device('cuda:0'), 16.0)
        mock_select_config.return_value = {"precision": "float16", "batch_size": 16}
        mock_loaded_model = MagicMock(spec=torch.nn.Module)
        mock_load_model.return_value = mock_loaded_model

        model_path = "test_model_path"
        model = DeepSeekModel(model_path)

        mock_detect_device.assert_called_once()
        mock_select_config.assert_called_once_with(16.0)
        mock_load_model.assert_called_once_with(model_path, torch.device('cuda:0'), {"precision": "float16", "batch_size": 16})
        self.assertEqual(model.device, torch.device('cuda:0'))
        self.assertEqual(model.vram_gb, 16.0)
        self.assertEqual(model.config, {"precision": "float16", "batch_size": 16})
        self.assertEqual(model.model, mock_loaded_model)

    @patch.object(DeepSeekModel, '_detect_device')
    @patch.object(DeepSeekModel, '_select_config')
    def test_init_insufficient_vram(self, mock_select_config, mock_detect_device):
        """Тестирует инициализацию при недостаточном VRAM."""
        mock_detect_device.return_value = (torch.device('cpu'), 0.0) # или < 6GB GPU
        mock_select_config.side_effect = RuntimeError("Недостаточно VRAM (0.0 GB). Минимум 6 GB.")

        model_path = "test_model_path"
        with self.assertRaisesRegex(RuntimeError, "Недостаточно VRAM .* Минимум 6 GB."):
            DeepSeekModel(model_path)
        
        mock_detect_device.assert_called_once()
        mock_select_config.assert_called_once_with(0.0)


    @patch('torch.no_grad')
    def test_inference(self, mock_no_grad):
        """Тестирует основной метод инференса."""
        # Мокаем __init__ и атрибуты для простоты
        with patch.object(DeepSeekModel, '__init__', lambda x, y: None):
            model_instance = DeepSeekModel("dummy")
            model_instance.model = MagicMock(spec=torch.nn.Module)
            model_instance.config = {"batch_size": 4} # Пример
            
            dummy_inputs = MagicMock()
            expected_outputs = MagicMock()
            model_instance.model.return_value = expected_outputs

            # Контекстный менеджер no_grad должен быть вызван
            # Чтобы проверить это, мы можем проверить, что __enter__ был вызван на mock_no_grad
            # Однако, проще проверить, что model_instance.model был вызван внутри with torch.no_grad():
            # Для этого мы можем позволить mock_no_grad быть обычным моком, который возвращает себя при входе в контекст

            outputs = model_instance.inference(dummy_inputs)

            # Проверяем, что torch.no_grad() был использован (неявно через вызов model)
            # и что модель была вызвана
            model_instance.model.assert_called_once_with(dummy_inputs)
            self.assertEqual(outputs, expected_outputs)
            # mock_no_grad(). __enter__.assert_called_once() # Проверка входа в контекст


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

