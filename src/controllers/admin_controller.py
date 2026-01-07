from sqlmodel import Session, select
from typing import List, Optional,Any,Dict
from fastapi import HTTPException, status
from datetime import datetime
import bcrypt

from ..models.user import User
from ..models.student import Student
from ..models.teacher import Teacher
from ..models.admin import Admin
from ..models.module import Module
from ..models.specialty import Specialty
from ..models.schedule import Schedule
from ..models.sday import SDay
from ..models.teacher_modules import TeacherModules
from ..models.attendance import AttendanceRecord
from ..models.enrollement import Enrollment
from ..models.session import Session as ClassSession
from ..models.enums import ScheduleDays, AttendanceStatus


class AdminController:
    """
    Admin Controller - Handles administrative operations
    
    Methods:
        Student Management:
        - add_student(): Add new student with specialty assignment
        - update_student(): Update existing student information
        - delete_student(): Delete a student
        
        Teacher Management:
        - add_teacher(): Add new teacher
        - update_teacher(): Update existing teacher information
        - delete_teacher(): Delete a teacher
        - assign_teacher_to_module(): Assign teacher to module
        
        Module Management:
        - create_module(): Create new module for specialty
        - update_module(): Update module information
        - delete_module(): Delete module
        
        Schedule Management:
        - make_schedule_for_specialty(): Create schedule for specialty
        - add_sday_to_schedule_of_specialty(): Add s_day to schedule
        - update_sday_of_schedule(): Update existing s_day
        - delete_sday_from_schedule(): Delete s_day from schedule
        
        Monitoring:
        - monitor_attendance(): Display all attendance records with details
        - generate_report(): Send attendance data to report controller
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # ==================== STUDENT MANAGEMENT ====================
    
    def add_student(
        self,
        full_name: str,
        email: str,
        password: str,
        department: str,
        specialty_id: int
    ) -> Student:
        """
        Add a new student with their information and assign a specialty.
        
        Args:
            full_name: Student's full name
            email: Student's email address
            password: Student's password (will be hashed)
            department: Student's department
            specialty_id: ID of the specialty to assign
            
        Returns:
            Student: The created student profile
        """
        # Check if specialty exists
        specialty = self.session.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialty with ID {specialty_id} not found"
            )
        
        # Check if email already exists
        existing_user = self.session.exec(
            select(User).where(User.email == email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user account
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=self._hash_password(password),
            department=department,
            role="student",
            is_active=True,
            is_verified=True
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        # Create student profile with specialty
        student = Student(
            user_id=user.id,
            specialty_id=specialty_id
        )
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        
        # Auto-enroll student in all modules of the specialty
        modules = self.session.exec(
            select(Module).where(Module.specialty_id == specialty_id)
        ).all()
        
        for module in modules:
            enrollment = Enrollment(
                student_id=student.id,
                module_id=module.id,
                is_excluded=False,
                student_name=full_name,
                student_email=email
            )
            self.session.add(enrollment)
        
        if modules:
            self.session.commit()
        
        return student
    
    def add_students(
        self,
        students_data: List[dict]
    ) -> Dict[str, Any]:
        """
        Add multiple students in bulk from JSON data.
        
        Args:
            students_data: List of student data dictionaries
                Each dict should have: full_name, email, password, department, specialty_id
        
        Returns:
            dict: Summary of added students with success/failure counts
            
        Example:
            students_data = [
                {"full_name": "John Doe", "email": "john@example.com", "password": "pass123", "department": "CS", "specialty_id": 1},
                {"full_name": "Jane Smith", "email": "jane@example.com", "password": "pass456", "department": "CS", "specialty_id": 1}
            ]
        """
        added_students = []
        failed = []
        
        for student_data in students_data:
            try:
                # Extract data from JSON
                full_name = student_data.get("full_name")
                email = student_data.get("email")
                password = student_data.get("password")
                department = student_data.get("department")
                specialty_id = student_data.get("specialty_id")
                
                # Validate required fields
                if not all([full_name, email, password, department, specialty_id]):
                    failed.append({
                        "data": student_data,
                        "error": "Missing required fields (full_name, email, password, department, specialty_id)"
                    })
                    continue
                
                # Call add_student function
                student = self.add_student(
                    full_name=full_name,
                    email=email,
                    password=password,
                    department=department,
                    specialty_id=specialty_id
                )
                
                added_students.append({
                    "student_id": student.id,
                    "full_name": full_name,
                    "email": email
                })
                
            except HTTPException as e:
                failed.append({
                    "data": student_data,
                    "error": e.detail
                })
            except Exception as e:
                failed.append({
                    "data": student_data,
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk student import completed",
            "total_processed": len(students_data),
            "successful": len(added_students),
            "failed": len(failed),
            "added_students": added_students,
            "failures": failed
        }
    
    def update_student(
        self,
        student_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        specialty_id: Optional[int] = None
    ) -> Student:
        """
        Update an existing student's information.
        
        Args:
            student_id: ID of the student to update
            full_name: New full name (optional)
            email: New email (optional)
            department: New department (optional)
            specialty_id: New specialty ID (optional)
            
        Returns:
            Student: Updated student profile
        """
        student = self.session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        user = self.session.get(User, student.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found"
            )
        
        # Update user info
        if full_name:
            user.full_name = full_name
        if email:
            user.email = email
        if department:
            user.department = department
        user.updated_at = datetime.utcnow()
        
        # Update specialty
        if specialty_id:
            specialty = self.session.get(Specialty, specialty_id)
            if not specialty:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Specialty with ID {specialty_id} not found"
                )
            student.specialty_id = specialty_id
        
        self.session.add(user)
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        
        return student
    
    def delete_student(self, student_id: int) -> dict:
        """
        Delete a student.
        
        Args:
            student_id: ID of the student to delete
            
        Returns:
            dict: Success message
        """
        student = self.session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        user = self.session.get(User, student.user_id)
        
        # Delete student profile first (foreign key constraint)
        self.session.delete(student)
        
        # Delete user account
        if user:
            self.session.delete(user)
        
        self.session.commit()
        
        return {"message": f"Student {student_id} deleted successfully"}
    
    # ==================== TEACHER MANAGEMENT ====================
    
    def add_teacher(
        self,
        full_name: str,
        email: str,
        password: str,
        department: str
    ) -> Teacher:
        """
        Add a new teacher.
        
        Args:
            full_name: Teacher's full name
            email: Teacher's email address
            password: Teacher's password (will be hashed)
            department: Teacher's department
            
        Returns:
            Teacher: The created teacher profile
        """
        # Check if email already exists
        existing_user = self.session.exec(
            select(User).where(User.email == email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user account
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=self._hash_password(password),
            department=department,
            role="teacher",
            is_active=True,
            is_verified=True
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        # Create teacher profile
        teacher = Teacher(user_id=user.id)
        self.session.add(teacher)
        self.session.commit()
        self.session.refresh(teacher)
        
        return teacher
    
    def update_teacher(
        self,
        teacher_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        department: Optional[str] = None
    ) -> Teacher:
        """
        Update an existing teacher's information.
        
        Args:
            teacher_id: ID of the teacher to update
            full_name: New full name (optional)
            email: New email (optional)
            department: New department (optional)
            
        Returns:
            Teacher: Updated teacher profile
        """
        teacher = self.session.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with ID {teacher_id} not found"
            )
        
        user = self.session.get(User, teacher.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found"
            )
        
        # Update user info
        if full_name:
            user.full_name = full_name
        if email:
            user.email = email
        if department:
            user.department = department
        user.updated_at = datetime.utcnow()
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(teacher)
        
        return teacher
    
    def delete_teacher(self, teacher_id: int) -> dict:
        """
        Delete a teacher.
        
        Args:
            teacher_id: ID of the teacher to delete
            
        Returns:
            dict: Success message
        """
        teacher = self.session.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with ID {teacher_id} not found"
            )
        
        user = self.session.get(User, teacher.user_id)
        
        # Delete teacher profile first (foreign key constraint)
        self.session.delete(teacher)
        
        # Delete user account
        if user:
            self.session.delete(user)
        
        self.session.commit()
        
        return {"message": f"Teacher {teacher_id} deleted successfully"}
    
    def assign_teacher_to_module(self, teacher_id: int, module_id: int) -> TeacherModules:
        """
        Assign a teacher to a module using the teacher_modules table.
        
        Args:
            teacher_id: ID of the teacher
            module_id: ID of the module
            
        Returns:
            TeacherModules: The created assignment
        """
        # Verify teacher exists
        teacher = self.session.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with ID {teacher_id} not found"
            )
        
        # Verify module exists
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        # Check if assignment already exists
        existing = self.session.exec(
            select(TeacherModules).where(
                TeacherModules.teacher_id == teacher_id,
                TeacherModules.module_id == module_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher is already assigned to this module"
            )
        
        # Create assignment
        teacher_module = TeacherModules(
            teacher_id=teacher_id,
            module_id=module_id
        )
        self.session.add(teacher_module)
        self.session.commit()
        self.session.refresh(teacher_module)
        
        return teacher_module
    
    # ==================== MODULE MANAGEMENT ====================
    
    def create_module(
        self,
        name: str,
        specialty_id: int,
        credits: Optional[int] = None,
        description: Optional[str] = None,
        semester: Optional[int] = None,
        room: Optional[str] = None
    ) -> Module:
        """
        Create a new module for a specialty.
        
        Args:
            name: Name of the module
            specialty_id: ID of the specialty
            credits: Number of credits
            description: Module description
            semester: Semester number
            room: Room/location
            
        Returns:
            Module: Created module
        """
        # Verify specialty exists
        specialty = self.session.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialty with ID {specialty_id} not found"
            )
        
        # Check if module with same name exists for this specialty
        existing = self.session.exec(
            select(Module).where(
                Module.name == name,
                Module.specialty_id == specialty_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Module '{name}' already exists for this specialty"
            )
        
        module = Module(
            name=name,
            specialty_id=specialty_id,
            credits=credits,
            description=description,
            semester=semester,
            room=room
        )
        
        self.session.add(module)
        self.session.commit()
        self.session.refresh(module)
        
        return module
    
    def update_module(
        self,
        module_id: int,
        name: Optional[str] = None,
        credits: Optional[int] = None,
        description: Optional[str] = None,
        semester: Optional[int] = None,
        room: Optional[str] = None
    ) -> Module:
        """
        Update an existing module.
        
        Args:
            module_id: ID of the module
            name: New name
            credits: New credits
            description: New description
            semester: New semester
            room: New room/location
            
        Returns:
            Module: Updated module
        """
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        if name:
            module.name = name
        if credits is not None:
            module.credits = credits
        if description:
            module.description = description
        if semester is not None:
            module.semester = semester
        if room:
            module.room = room
        
        self.session.add(module)
        self.session.commit()
        self.session.refresh(module)
        
        return module
    
    def delete_module(self, module_id: int) -> dict:
        """
        Delete a module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            dict: Success message
        """
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        # Check if module has enrollments
        enrollments = self.session.exec(
            select(Enrollment).where(Enrollment.module_id == module_id)
        ).all()
        
        if enrollments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete module with existing enrollments"
            )
        
        self.session.delete(module)
        self.session.commit()
        
        return {"message": f"Module '{module.name}' deleted successfully"}
    
    # ==================== SCHEDULE MANAGEMENT ====================
    
    def make_schedule_for_specialty(self, specialty_id: int) -> Schedule:
        """
        Create a schedule for a specialty.
        
        Args:
            specialty_id: ID of the specialty
            
        Returns:
            Schedule: The created schedule
        """
        # Verify specialty exists
        specialty = self.session.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialty with ID {specialty_id} not found"
            )
        
        # Check if schedule already exists
        existing = self.session.exec(
            select(Schedule).where(Schedule.specialty_id == specialty_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule already exists for this specialty"
            )
        
        # Create schedule
        schedule = Schedule(
            specialty_id=specialty_id,
            last_updated=datetime.utcnow()
        )
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        
        return schedule
    
    def add_sday_to_schedule_of_specialty(
        self,
        specialty_id: int,
        day: ScheduleDays,
        time: str,
        module_id: int
    ) -> SDay:
        """
        Add an s_day to the schedule of a specialty.
        Module must have the same specialty_id as the specialty.
        
        Args:
            specialty_id: ID of the specialty
            day: Day of the week (ScheduleDays enum)
            time: Time string (e.g., "08:00-10:00")
            module_id: ID of the module
            
        Returns:
            SDay: The created s_day
        """
        # Get schedule for specialty
        schedule = self.session.exec(
            select(Schedule).where(Schedule.specialty_id == specialty_id)
        ).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No schedule found for specialty {specialty_id}. Create one first."
            )
        
        # Verify module exists and belongs to same specialty
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        if module.specialty_id != specialty_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Module specialty ({module.specialty_id}) does not match schedule specialty ({specialty_id})"
            )
        
        # Create s_day
        sday = SDay(
            day=day,
            time=time,
            schedule_id=schedule.id,
            module_id=module_id
        )
        self.session.add(sday)
        
        # Update schedule last_updated
        schedule.last_updated = datetime.utcnow()
        self.session.add(schedule)
        
        self.session.commit()
        self.session.refresh(sday)
        
        return sday
    
    def update_sday_of_schedule(
        self,
        sday_id: int,
        day: Optional[ScheduleDays] = None,
        time: Optional[str] = None,
        module_id: Optional[int] = None
    ) -> SDay:
        """
        Update an existing s_day in the schedule.
        
        Args:
            sday_id: ID of the s_day to update
            day: New day (optional)
            time: New time (optional)
            module_id: New module ID (optional)
            
        Returns:
            SDay: Updated s_day
        """
        sday = self.session.get(SDay, sday_id)
        if not sday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SDay with ID {sday_id} not found"
            )
        
        schedule = self.session.get(Schedule, sday.schedule_id)
        
        if day:
            sday.day = day
        if time:
            sday.time = time
        if module_id:
            # Verify module belongs to same specialty
            module = self.session.get(Module, module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Module with ID {module_id} not found"
                )
            if schedule and module.specialty_id != schedule.specialty_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Module specialty does not match schedule specialty"
                )
            sday.module_id = module_id
        
        # Update schedule last_updated
        if schedule:
            schedule.last_updated = datetime.utcnow()
            self.session.add(schedule)
        
        self.session.add(sday)
        self.session.commit()
        self.session.refresh(sday)
        
        return sday
    
    def delete_sday_from_schedule(self, sday_id: int) -> dict:
        """
        Delete an s_day from the schedule.
        
        Args:
            sday_id: ID of the s_day to delete
            
        Returns:
            dict: Success message
        """
        sday = self.session.get(SDay, sday_id)
        if not sday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SDay with ID {sday_id} not found"
            )
        
        schedule = self.session.get(Schedule, sday.schedule_id)
        
        self.session.delete(sday)
        
        # Update schedule last_updated
        if schedule:
            schedule.last_updated = datetime.utcnow()
            self.session.add(schedule)
        
        self.session.commit()
        
        return {"message": f"SDay {sday_id} deleted successfully"}
    
    # ==================== MONITORING & REPORTING ====================
    
    def monitor_attendance(self) -> dict:
        """
        Display ALL system data: specialties, students, modules, teachers,
        teacher assignments, sessions, and attendance records.
        
        Returns:
            dict: Complete system data organized by specialty
        """
        # Get all specialties
        specialties = self.session.exec(select(Specialty)).all()
        
        system_data = {
            "specialties": [],
            "summary": {
                "total_specialties": 0,
                "total_students": 0,
                "total_teachers": 0,
                "total_modules": 0,
                "total_sessions": 0,
                "total_attendance_records": 0,
                "attendance_stats": {
                    "present": 0,
                    "absent": 0,
                    "justified": 0,
                    "excluded": 0
                }
            }
        }
        
        all_teacher_ids = set()
        
        for specialty in specialties:
            specialty_data = {
                "id": specialty.id,
                "name": specialty.name,
                "year_level": specialty.year_level,
                "students": [],
                "modules": [],
                "schedule": None
            }
            
            # Get students in this specialty
            students = self.session.exec(
                select(Student).where(Student.specialty_id == specialty.id)
            ).all()
            
            for student in students:
                student_user = self.session.get(User, student.user_id)
                
                # Get student enrollments
                enrollments = self.session.exec(
                    select(Enrollment).where(Enrollment.student_id == student.id)
                ).all()
                
                student_enrollments = []
                for enrollment in enrollments:
                    module = self.session.get(Module, enrollment.module_id)
                    
                    # Get attendance records for this enrollment
                    attendance_records = self.session.exec(
                        select(AttendanceRecord).where(
                            AttendanceRecord.enrollement_id == enrollment.id
                        )
                    ).all()
                    
                    enrollment_attendance = []
                    for record in attendance_records:
                        session_obj = self.session.get(ClassSession, record.session_id)
                        enrollment_attendance.append({
                            "record_id": record.id,
                            "session_id": record.session_id,
                            "session_date": session_obj.date_time if session_obj else None,
                            "status": record.status.value if record.status else "ABSENT",
                            "created_at": record.created_at
                        })
                        
                        # Update summary stats
                        system_data["summary"]["total_attendance_records"] += 1
                        if record.status == AttendanceStatus.PRESENT:
                            system_data["summary"]["attendance_stats"]["present"] += 1
                        elif record.status == AttendanceStatus.ABSENT:
                            system_data["summary"]["attendance_stats"]["absent"] += 1
                        elif record.status == AttendanceStatus.JUSTIFIED:
                            system_data["summary"]["attendance_stats"]["justified"] += 1
                        elif record.status == AttendanceStatus.EXCLUDED:
                            system_data["summary"]["attendance_stats"]["excluded"] += 1
                    
                    student_enrollments.append({
                        "enrollment_id": enrollment.id,
                        "module_id": enrollment.module_id,
                        "module_name": module.name if module else None,
                        "is_excluded": enrollment.is_excluded,
                        "attendance_records": enrollment_attendance
                    })
                
                specialty_data["students"].append({
                    "id": student.id,
                    "user_id": student.user_id,
                    "name": student_user.full_name if student_user else None,
                    "email": student_user.email if student_user else None,
                    "enrollments": student_enrollments
                })
                system_data["summary"]["total_students"] += 1
            
            # Get modules in this specialty
            modules = self.session.exec(
                select(Module).where(Module.specialty_id == specialty.id)
            ).all()
            
            for module in modules:
                # Get teachers assigned to this module
                teacher_modules = self.session.exec(
                    select(TeacherModules).where(TeacherModules.module_id == module.id)
                ).all()
                
                module_teachers = []
                for tm in teacher_modules:
                    teacher = self.session.get(Teacher, tm.teacher_id)
                    teacher_user = self.session.get(User, teacher.user_id) if teacher else None
                    all_teacher_ids.add(tm.teacher_id)
                    
                    # Get sessions created by this teacher for this module
                    sessions = self.session.exec(
                        select(ClassSession).where(
                            ClassSession.teacher_module_id == tm.id
                        )
                    ).all()
                    
                    teacher_sessions = []
                    for sess in sessions:
                        # Get attendance summary for this session
                        sess_attendance = self.session.exec(
                            select(AttendanceRecord).where(
                                AttendanceRecord.session_id == sess.id
                            )
                        ).all()
                        
                        present_count = sum(1 for r in sess_attendance if r.status == AttendanceStatus.PRESENT)
                        absent_count = sum(1 for r in sess_attendance if r.status == AttendanceStatus.ABSENT)
                        
                        teacher_sessions.append({
                            "session_id": sess.id,
                            "session_code": sess.session_code,
                            "date_time": sess.date_time,
                            "duration_minutes": sess.duration_minutes,
                            "is_active": sess.is_active,
                            "attendance_summary": {
                                "total": len(sess_attendance),
                                "present": present_count,
                                "absent": absent_count
                            }
                        })
                        system_data["summary"]["total_sessions"] += 1
                    
                    module_teachers.append({
                        "teacher_module_id": tm.id,
                        "teacher_id": teacher.id if teacher else None,
                        "name": teacher_user.full_name if teacher_user else None,
                        "email": teacher_user.email if teacher_user else None,
                        "sessions": teacher_sessions
                    })
                
                specialty_data["modules"].append({
                    "id": module.id,
                    "name": module.name,
                    "code": module.code,
                    "credits": module.credits,
                    "teachers": module_teachers
                })
                system_data["summary"]["total_modules"] += 1
            
            # Get schedule for this specialty
            schedule = self.session.exec(
                select(Schedule).where(Schedule.specialty_id == specialty.id)
            ).first()
            
            if schedule:
                sdays = self.session.exec(
                    select(SDay).where(SDay.schedule_id == schedule.id)
                ).all()
                
                schedule_days = []
                for sday in sdays:
                    module = self.session.get(Module, sday.module_id)
                    schedule_days.append({
                        "id": sday.id,
                        "day": sday.day.value if sday.day else None,
                        "time": sday.time,
                        "module_id": sday.module_id,
                        "module_name": module.name if module else None
                    })
                
                specialty_data["schedule"] = {
                    "id": schedule.id,
                    "last_updated": schedule.last_updated,
                    "days": schedule_days
                }
            
            system_data["specialties"].append(specialty_data)
            system_data["summary"]["total_specialties"] += 1
        
        system_data["summary"]["total_teachers"] = len(all_teacher_ids)
        
        # Calculate attendance rate
        total_records = system_data["summary"]["total_attendance_records"]
        if total_records > 0:
            system_data["summary"]["attendance_rate"] = round(
                (system_data["summary"]["attendance_stats"]["present"] / total_records * 100), 2
            )
        else:
            system_data["summary"]["attendance_rate"] = 0
        
        return system_data
    
    def generate_report(self, admin_id: int, period_start: datetime, period_end: datetime) -> dict:
        """
        Generate report with PDF and Excel files saved to uploads/reports/
        
        Workflow:
            1. Get all system data via monitor_attendance()
            2. Filter by period
            3. Send to ReportController to create PDF/Excel
            4. ReportController saves files and URLs in Report model
        
        Args:
            admin_id: ID of the admin
            period_start: Report period start
            period_end: Report period end
            
        Returns:
            dict: Report info with file URLs
        """
        # Verify admin exists
        admin = self.session.get(Admin, admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin with ID {admin_id} not found"
            )
        
        # Get all system data
        system_data = self.monitor_attendance()
        
        # Filter by period and calculate stats
        filtered_specialties = []
        period_stats = {
            "total_attendance_records": 0,
            "present": 0,
            "absent": 0,
            "justified": 0,
            "excluded": 0
        }
        
        for specialty in system_data["specialties"]:
            filtered_specialty = specialty.copy()
            filtered_students = []
            
            for student in specialty["students"]:
                filtered_student = student.copy()
                filtered_enrollments = []
                
                for enrollment in student["enrollments"]:
                    filtered_enrollment = enrollment.copy()
                    filtered_records = []
                    
                    for record in enrollment["attendance_records"]:
                        record_date = record.get("session_date") or record.get("created_at")
                        if record_date and period_start <= record_date <= period_end:
                            filtered_records.append(record)
                            period_stats["total_attendance_records"] += 1
                            status_val = record.get("status", "ABSENT")
                            if status_val == "PRESENT":
                                period_stats["present"] += 1
                            elif status_val == "ABSENT":
                                period_stats["absent"] += 1
                            elif status_val == "JUSTIFIED":
                                period_stats["justified"] += 1
                            elif status_val == "EXCLUDED":
                                period_stats["excluded"] += 1
                    
                    filtered_enrollment["attendance_records"] = filtered_records
                    filtered_enrollments.append(filtered_enrollment)
                
                filtered_student["enrollments"] = filtered_enrollments
                filtered_students.append(filtered_student)
            
            filtered_specialty["students"] = filtered_students
            filtered_specialties.append(filtered_specialty)
        
        # Calculate attendance rate
        if period_stats["total_attendance_records"] > 0:
            period_stats["attendance_rate"] = round(
                (period_stats["present"] / period_stats["total_attendance_records"] * 100), 2
            )
        else:
            period_stats["attendance_rate"] = 0
        
        report_data = {
            "specialties": filtered_specialties,
            "period_summary": period_stats
        }
        
        # Send to ReportController - creates PDF/Excel and saves to uploads/reports/
        from .report_controller import ReportController
        report_controller = ReportController(self.session)
        
        return report_controller.generate_report(
            admin_id=admin_id,
            report_data=report_data,
            period_start=period_start,
            period_end=period_end
        )
