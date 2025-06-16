from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import redirect
import re
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import os
import joblib
from django.conf import settings
from .models import FootandMouth
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from PIL import Image  
from torchvision import transforms
import numpy as np
import onnxruntime as ort



rf_model_path = os.path.join(settings.BASE_DIR, 'FMD', 'ml_models', 'tuned_XGBoost_model.pkl')
rf_model = joblib.load(rf_model_path)




# Create your views here.
def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

        if not re.match(email_pattern, email):
            return HttpResponse("Invalid email format")
        if pass1 != pass2:
            return HttpResponse("Your passwords do not match")
        if not re.match(password_pattern, pass1):
            return HttpResponse(
                "Password must be at least 8 characters long, "
                "include at least one uppercase letter, one lowercase letter, "
                "one number, and one special character"
            )

        my_user = User.objects.create_user(uname, email, pass1)
        my_user.save()
        return redirect('login')
    return render(request, 'signup.html')


def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass')
        user = authenticate(request, username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error_message': 'username or password is incorrect!!'})
    return render(request, 'login.html')

def LogoutPage(request):
    logout(request)
    return redirect('login')
def HomePage(request):
    return render(request, 'homepage.html')


@login_required(login_url='login')
def PredictView(request):
    prediction = None
    error = None
    if request.method == 'POST':
        try:
            current_reference = float(request.POST.get('current_reference'))
            year = int(request.POST.get('year'))
            cattle_density = int(request.POST.get('cattle_density'))
            rainfall = float(request.POST.get('rainfall'))
            max_temp = float(request.POST.get('max_temp'))
            adjacent_national_parks = float(request.POST.get('adjacent_national_parks')) 
            international_boarder = float(request.POST.get('international_boarder'))

            prediction = rf_model.predict([[cattle_density, rainfall, max_temp, adjacent_national_parks, international_boarder]])[0]

            FootandMouth.objects.create(
                user=request.user,
                current_reference=current_reference, year=year, cattle_density=cattle_density,
                rainfall=rainfall, max_temp=max_temp,
                adjacent_national_parks=adjacent_national_parks, international_boarder=international_boarder, 
                prediction=prediction
            )

        except (TypeError, ValueError) as e:
            error = "Invalid input. Please ensure all fields are filled in correctly."
    
    return render(request, 'predict.html', {'prediction': prediction, 'error': error})

def Image_detection(request):
    return render(request, 'Image_detection.html')




# Image transformation (same as training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def Image_detection(request):
    prediction = None
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        full_path = fs.path(file_path)

        # Load and preprocess image
        image = Image.open(full_path).convert('RGB')
        image = transform(image)
        image = image.unsqueeze(0).numpy()

        # Load ONNX model
        model_path = os.path.join('FMD', 'ml_models', 'FMD_resnet50_model.onnx')
        session = ort.InferenceSession(model_path)
        input_name = session.get_inputs()[0].name

        # Run inference
        outputs = session.run(None, {input_name: image})
        pred_class = np.argmax(outputs[0])

        prediction = int(pred_class)

        # Delete uploaded image after prediction (optional)
        os.remove(full_path)

    return render(request, 'Image_detection.html', {'prediction': prediction})