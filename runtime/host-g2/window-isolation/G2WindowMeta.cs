using System;
using System.Runtime.InteropServices;
using System.Text;
public static class G2WindowMeta {
 [DllImport("user32.dll")] public static extern IntPtr GetProcessWindowStation();
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool GetUserObjectInformation(IntPtr h,int kind,StringBuilder value,uint length,out uint needed);
 [DllImport("user32.dll",SetLastError=true)] static extern bool GetUserObjectInformation(IntPtr h,int kind,IntPtr value,uint length,out uint needed);
 public static string Name(){var b=new StringBuilder(256);uint n;if(!GetUserObjectInformation(GetProcessWindowStation(),2,b,512,out n))throw new Exception("UOI name:"+Marshal.GetLastWin32Error());return b.ToString();}
 public static bool Visible(){uint n;IntPtr b=Marshal.AllocHGlobal(12);try{if(!GetUserObjectInformation(GetProcessWindowStation(),1,b,12,out n))throw new Exception("UOI flags:"+Marshal.GetLastWin32Error());return (Marshal.ReadInt32(b,8)&1)!=0;}finally{Marshal.FreeHGlobal(b);}}
}
