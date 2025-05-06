from typing import Dict, Any, Type, TypeVar, cast
from functools import lru_cache

T = TypeVar('T')

class ServiceRegistry:
    """
    A centralized registry for application services.
    Enables clean dependency injection and service discovery.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, service_name: str, service_instance: Any) -> None:
        """
        Register a service instance with the registry.
        
        Args:
            service_name: Unique name for the service
            service_instance: The service instance to register
        """
        self._services[service_name] = service_instance
    
    def register_factory(self, service_name: str, factory: callable) -> None:
        """
        Register a factory function to create a service on demand.
        
        Args:
            service_name: Unique name for the service
            factory: Function that creates the service instance
        """
        self._factories[service_name] = factory
    
    def get(self, service_name: str) -> Any:
        """
        Get a service instance by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            KeyError: If service is not found
        """
        if service_name in self._services:
            return self._services[service_name]
        
        if service_name in self._factories:
            # Create service on demand
            service = self._factories[service_name]()
            self._services[service_name] = service
            return service
        
        raise KeyError(f"Service '{service_name}' not registered")
    
    def get_by_type(self, service_type: Type[T]) -> T:
        """
        Get a service instance by its type.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            The service instance of the specified type
            
        Raises:
            ValueError: If no service of that type is found
        """
        for service in self._services.values():
            if isinstance(service, service_type):
                return cast(T, service)
        
        # Try to create from factories
        for factory in self._factories.values():
            service = factory()
            if isinstance(service, service_type):
                self._services[service_type.__name__] = service
                return cast(T, service)
        
        raise ValueError(f"No service of type '{service_type.__name__}' registered")
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()


@lru_cache
def get_registry() -> ServiceRegistry:
    """
    Singleton accessor for the service registry.
    
    Returns:
        The application's service registry instance
    """
    return ServiceRegistry()