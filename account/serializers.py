from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


User = get_user_model()

class UserRegistrationSerializers(serializers.ModelSerializer):
  email = serializers.EmailField(required=True,validators=[UniqueValidator(queryset=User.objects.all())])
  
  password = serializers.CharField(
    write_only=True,required=True,validators = [validate_password],style={'input_type':'password'}
  )
  
  password2 = serializers.CharField(
    write_only=True,required=True,style={'input_type':'password'}
  )
  
  first_name = serializers.CharField(max_length=255)
  last_name = serializers.CharField(max_length=255)
  
  
  class Meta:
    model = User
    fields = ["email","first_name","last_name","password","password2"]
    
    
  def validate(self, attrs):
    if attrs['password'] != attrs['password2']:
      raise serializers.ValidationError({"password":"password doesnot match."})
    return attrs
  
  def create(self, validated_data):
    validated_data.pop('password2')
    email = validated_data['email']
    username = email.split('@')[0]
    
    # Ensure unique username
    base_username = username
    counter =1
    while User.objects.filter(username=username).exists():
      username = f"{base_username}{counter}"
      counter += 1
      
    user = User.objects.create_user(
      email=email,
      password=validated_data['password'],
      username=username,
      first_name = validated_data['first_name'],
      last_name = validated_data['last_name']
    )
    
    return user
  
class LoginUserSerializers(serializers.Serializer):
  email = serializers.EmailField(required=True)
  password = serializers.CharField(max_length=255,write_only=True,style={'input-type':'password'})
  
  def validate(self, attrs):
    email = attrs.get('email')
    password = attrs.get('password')
    if email and password:
      user = authenticate(request=self.context.get('request'),email=email,password=password)
      if not user:
        raise serializers.ValidationError({"error":_("Invalid email or password ")})
      
      if not user.is_active:
        raise serializers.ValidationError({"message":_("Account is not activated")})
      
    else:
      raise serializers.ValidationError({"error":_("Must include both email and password")})
    
    attrs['user'] = user
    return attrs
  

    
    
    
    
    
    
    