from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
# Create your models here.
class CustomUserManager(BaseUserManager):
  def create_user(self,email,username,first_name,last_name,password=None):
    if not email:
      raise ValueError("Users must have an email address")
    
    if not username:
      raise ValueError("Users must have an username address")
    
    user = self.model(
      email = self.normalize_email(email),
      username=username,
      first_name=first_name,
      last_name=last_name
      
    )
    user.set_password(password)
    user.save(using=self._db)
    return user
  
  def create_superuser(self,email,username,first_name,last_name,password=None):
    user = self.create_user(
      email=email,
      username=username,
      first_name=first_name,
      last_name=last_name,
      password=password
    )
    
    user.is_admin = True
    user.is_staff = True
    user.is_active = True
    user.is_superadmin = True
    user.save(using=self._db)
    return user
  


class CustomUser(AbstractBaseUser):
  email = models.EmailField(max_length=255,unique=True)
  username = models.CharField(max_length=255,unique=True)
  first_name = models.CharField(max_length=255,null=True,blank=True)
  last_name = models.CharField(max_length=255,null=True,blank=True)
  date_joined = models.DateTimeField(auto_now_add=True)
  last_login = models.DateTimeField(auto_now=True)
  is_active = models.BooleanField(default=False)
  is_admin = models.BooleanField(default=False)
  is_staff = models.BooleanField(default=False)
  is_superadmin = models.BooleanField(default=False)

  
  objects = CustomUserManager()
  
  USERNAME_FIELD = "email"
  REQUIRED_FIELDS = ["first_name","last_name","username"]
  
  def __str__(self):
    return self.email
  
  def has_perm(self, perm, obj=None):
        #"Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
    return self.is_admin

  def has_module_perms(self, app_label):
    #"Does the user have permissions to view the app `app_label`?"
    # Simplest possible answer: Yes, always
    return True
  