# ============= config/di_container.py =============
"""
Dependency Injection Container

This module provides a simple service container for dependency injection.
It allows for loose coupling between components and makes testing easier.
"""

from typing import TypeVar, Type, Dict, Any, Optional, Callable
from functools import lru_cache
import threading

T = TypeVar('T')


class DIContainer:
    """
    Simple dependency injection container.
    
    This container manages service instances and provides dependency resolution.
    It supports:
    - Singleton services (one instance per application)
    - Factory services (new instance each time)
    - Lazy loading (service created only when needed)
    
    Example:
        container = DIContainer()
        
        # Register a singleton service
        container.register_singleton(ETOCalculator, ETOCalculator())
        
        # Register a factory
        container.register_factory(Database, lambda: Database())
        
        # Resolve a service
        calc = container.resolve(ETOCalculator)
    """
    
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._lock = threading.Lock()
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """
        Register a singleton service.
        
        Args:
            interface: The interface/type to register
            instance: The singleton instance
        """
        with self._lock:
            self._singletons[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for creating instances.
        
        Args:
            interface: The interface/type to register
            factory: A callable that returns an instance
        """
        with self._lock:
            self._factories[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service from the container.
        
        Args:
            interface: The interface/type to resolve
            
        Returns:
            An instance of the requested service
            
        Raises:
            KeyError: If the service is not registered
        """
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check factories
        if interface in self._factories:
            return self._factories[interface]()
        
        # Not found
        raise KeyError(f"Service {interface.__name__} is not registered. "
                      f"Available: {list(self._singletons.keys()) + list(self._factories.keys())}")
    
    def clear(self) -> None:
        """Clear all registered services"""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
    
    def has(self, interface: Type[T]) -> bool:
        """Check if a service is registered"""
        return interface in self._singletons or interface in self._factories


# Global container instance
_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """Get the global container instance"""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DIContainer()
                _register_default_services(_container)
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)"""
    global _container
    with _container_lock:
        if _container:
            _container.clear()
        _container = None


def _register_default_services(container: DIContainer) -> None:
    """
    Register default services in the container.
    
    This is called automatically when the container is first accessed.
    """
    # Core services - singletons
    from src.core.eto_calculator import ETOCalculator
    container.register_singleton(ETOCalculator, ETOCalculator())
    
    # Database session factory
    from config.database import SessionLocal
    container.register_factory(type(SessionLocal), lambda: SessionLocal)
    
    # Configuration
    from config.app_config import get_config
    container.register_factory(type(get_config), lambda: get_config)


# Convenience methods for common services
@lru_cache(maxsize=1)
def get_eto_calculator() -> 'ETOCalculator':
    """Get the ETo calculator singleton"""
    from src.core.eto_calculator import ETOCalculator
    return ETOCalculator()


@lru_cache(maxsize=1)
def get_crop_database() -> 'CropDatabase':
    """Get the crop database singleton"""
    from src.models.crop import CropDatabase
    return CropDatabase()


@lru_cache(maxsize=1)
def get_soil_database() -> 'SoilDatabase':
    """Get the soil database singleton"""
    from src.models.soil import SoilDatabase
    return SoilDatabase()


def get_database_session():
    """Get a new database session"""
    from config.database import SessionLocal
    return SessionLocal()


# Service locator pattern for backward compatibility
class ServiceLocator:
    """
    Service locator for accessing common services.
    
    This provides backward compatibility while encouraging
    direct dependency injection for new code.
    """
    
    @staticmethod
    def get_eto_calculator() -> 'ETOCalculator':
        """Get ETo calculator"""
        return get_eto_calculator()
    
    @staticmethod
    def get_crop_database() -> 'CropDatabase':
        """Get crop database"""
        return get_crop_database()
    
    @staticmethod
    def get_soil_database() -> 'SoilDatabase':
        """Get soil database"""
        return get_soil_database()
    
    @staticmethod
    def get_database_session():
        """Get database session"""
        return get_database_session()
    
    @staticmethod
    def get_config():
        """Get application config"""
        from config.app_config import get_config
        return get_config()


__all__ = [
    'DIContainer',
    'get_container',
    'reset_container',
    'get_eto_calculator',
    'get_crop_database',
    'get_soil_database',
    'get_database_session',
    'ServiceLocator',
]
