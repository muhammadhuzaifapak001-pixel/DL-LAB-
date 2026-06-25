"""
Unit tests for plant disease detection models.
Run with: pytest tests/ -v --cov=src --cov=deployment
"""

import json
import tempfile
from pathlib import Path

import pytest
import torch

from src.data_loader import get_transforms
from src.evaluate import evaluate_model
from src.model import BaselineCNN, ImprovedCNN, get_model


class TestModels:
    """Test CNN model architectures."""
    
    def test_baseline_instantiation(self):
        """Test BaselineCNN can be created."""
        model = BaselineCNN(num_classes=15)
        assert model is not None
        assert isinstance(model, torch.nn.Module)
    
    def test_improved_instantiation(self):
        """Test ImprovedCNN can be created."""
        model = ImprovedCNN(num_classes=15)
        assert model is not None
        assert isinstance(model, torch.nn.Module)
    
    def test_baseline_output_shape(self):
        """Test BaselineCNN produces correct output shape."""
        model = BaselineCNN(num_classes=15)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 15)
    
    def test_improved_output_shape(self):
        """Test ImprovedCNN produces correct output shape."""
        model = ImprovedCNN(num_classes=15)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 15)
    
    def test_baseline_forward_pass(self):
        """Test BaselineCNN forward pass doesn't raise errors."""
        model = BaselineCNN(num_classes=15)
        x = torch.randn(4, 3, 224, 224)
        out = model(x)
        assert not torch.isnan(out).any()
        assert out.shape[0] == 4
    
    def test_improved_forward_pass(self):
        """Test ImprovedCNN forward pass doesn't raise errors."""
        model = ImprovedCNN(num_classes=15)
        x = torch.randn(4, 3, 224, 224)
        out = model(x)
        assert not torch.isnan(out).any()
        assert out.shape[0] == 4
    
    def test_get_model_v1(self):
        """Test get_model returns correct v1 model."""
        model = get_model(version="v1", num_classes=15)
        assert isinstance(model, BaselineCNN)
    
    def test_get_model_v2(self):
        """Test get_model returns correct v2 model."""
        model = get_model(version="v2", num_classes=15)
        assert isinstance(model, ImprovedCNN)
    
    def test_get_model_different_classes(self):
        """Test models work with different number of classes."""
        for num_classes in [5, 10, 20]:
            model_v1 = get_model(version="v1", num_classes=num_classes)
            model_v2 = get_model(version="v2", num_classes=num_classes)
            
            x = torch.randn(2, 3, 224, 224)
            out_v1 = model_v1(x)
            out_v2 = model_v2(x)
            
            assert out_v1.shape == (2, num_classes)
            assert out_v2.shape == (2, num_classes)
    
    def test_model_trainable(self):
        """Test model parameters are trainable."""
        model = BaselineCNN(num_classes=15)
        for param in model.parameters():
            assert param.requires_grad is True
    
    def test_improved_deeper_than_baseline(self):
        """Test ImprovedCNN has more parameters than BaselineCNN."""
        v1 = BaselineCNN(num_classes=15)
        v2 = ImprovedCNN(num_classes=15)
        
        v1_params = sum(p.numel() for p in v1.parameters())
        v2_params = sum(p.numel() for p in v2.parameters())
        
        assert v2_params > v1_params


class TestTransforms:
    """Test data augmentation transforms."""
    
    def test_transforms_exist(self):
        """Test that train and eval transforms are returned."""
        train_transform, eval_transform = get_transforms()
        assert train_transform is not None
        assert eval_transform is not None
    
    def test_train_transform_has_augmentation(self):
        """Test that train transform includes augmentation."""
        train_transform, _ = get_transforms()
        transform_names = [t.__class__.__name__ for t in train_transform.transforms]
        
        assert "RandomHorizontalFlip" in transform_names
        assert "RandomVerticalFlip" in transform_names
        assert "RandomRotation" in transform_names
        assert "ColorJitter" in transform_names
    
    def test_eval_transform_no_augmentation(self):
        """Test that eval transform doesn't have augmentation."""
        _, eval_transform = get_transforms()
        transform_names = [t.__class__.__name__ for t in eval_transform.transforms]
        
        # Should not have augmentation, only resize and normalize
        assert "RandomHorizontalFlip" not in transform_names
        assert "RandomVerticalFlip" not in transform_names


class TestEvaluation:
    """Test evaluation metrics."""
    
    def test_evaluate_model_basic(self):
        """Test evaluate_model function works."""
        model = BaselineCNN(num_classes=15)
        model.eval()
        
        # Create dummy data
        x = torch.randn(4, 3, 224, 224)
        y = torch.randint(0, 15, (4,))
        
        # Create dummy dataloader
        from torch.utils.data import DataLoader, TensorDataset
        dataset = TensorDataset(x, y)
        dataloader = DataLoader(dataset, batch_size=2)
        
        criterion = torch.nn.CrossEntropyLoss()
        device = torch.device("cpu")
        
        loss, accuracy = evaluate_model(model, dataloader, criterion, device)
        
        assert isinstance(loss, float)
        assert isinstance(accuracy, float)
        assert loss >= 0
        assert 0 <= accuracy <= 100
    
    def test_evaluate_model_returns_scalars(self):
        """Test evaluate_model returns scalar values."""
        model = ImprovedCNN(num_classes=10)
        model.eval()
        
        x = torch.randn(8, 3, 224, 224)
        y = torch.randint(0, 10, (8,))
        
        from torch.utils.data import DataLoader, TensorDataset
        dataset = TensorDataset(x, y)
        dataloader = DataLoader(dataset, batch_size=4)
        
        criterion = torch.nn.CrossEntropyLoss()
        device = torch.device("cpu")
        
        loss, accuracy = evaluate_model(model, dataloader, criterion, device)
        
        assert not torch.is_tensor(loss)
        assert not torch.is_tensor(accuracy)


class TestDeploymentUtils:
    """Test deployment utilities."""
    
    def test_preprocess_image_import(self):
        """Test image preprocessing function can be imported."""
        from deployment.utils import preprocess_image
        assert callable(preprocess_image)
    
    def test_predict_image_import(self):
        """Test prediction function can be imported."""
        from deployment.utils import predict_image
        assert callable(predict_image)
    
    def test_load_class_names(self):
        """Test loading class names JSON."""
        from deployment.utils import load_class_names
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_classes = ["class_0", "class_1", "class_2"]
            json.dump(test_classes, f)
            temp_path = Path(f.name)
        
        try:
            classes = load_class_names(temp_path)
            assert classes == test_classes
            assert len(classes) == 3
        finally:
            temp_path.unlink()
    
    def test_load_class_names_missing_file(self):
        """Test loading class names from non-existent file raises error."""
        from deployment.utils import load_class_names
        
        with pytest.raises(FileNotFoundError):
            load_class_names(Path("/non/existent/path/classes.json"))


class TestAPIEndpoints:
    """Test FastAPI endpoints (basic validation)."""
    
    def test_app_import(self):
        """Test FastAPI app can be imported."""
        from deployment.app import app
        assert app is not None
    
    def test_model_get_function(self):
        """Test get_model function is accessible."""
        from src.model import get_model
        model = get_model(version="v1", num_classes=15)
        assert model is not None


class TestDataValidation:
    """Test data validation and handling."""
    
    def test_model_batch_processing(self):
        """Test models handle variable batch sizes."""
        model_v1 = BaselineCNN(num_classes=15)
        model_v2 = ImprovedCNN(num_classes=15)
        
        for batch_size in [1, 2, 8, 16, 32]:
            x = torch.randn(batch_size, 3, 224, 224)
            
            out_v1 = model_v1(x)
            out_v2 = model_v2(x)
            
            assert out_v1.shape[0] == batch_size
            assert out_v2.shape[0] == batch_size
    
    def test_model_different_input_sizes_fail(self):
        """Test models fail gracefully with wrong input dimensions."""
        model = BaselineCNN(num_classes=15)
        
        # Wrong number of channels
        with pytest.raises((RuntimeError, ValueError)):
            x = torch.randn(2, 1, 224, 224)  # 1 channel instead of 3
            model(x)


class TestModelSerialization:
    """Test model saving and loading."""
    
    def test_save_and_load_model(self):
        """Test models can be saved and loaded."""
        model = BaselineCNN(num_classes=15)
        
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Save
            torch.save(model.state_dict(), temp_path)
            assert temp_path.exists()
            
            # Load
            new_model = BaselineCNN(num_classes=15)
            new_model.load_state_dict(torch.load(temp_path))
            
            # Verify parameters match
            for p1, p2 in zip(model.parameters(), new_model.parameters()):
                assert torch.equal(p1, p2)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
