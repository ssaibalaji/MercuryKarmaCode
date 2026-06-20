import { GradientButton } from '../ui/GradientButton';
import { authService } from '../../services/authService';

export function GoogleLoginButton(): JSX.Element {
  const handleClick = (): void => {
    window.location.href = authService.googleLoginUrl();
  };

  return (
    <GradientButton type="button" onClick={handleClick} w="full" bgGradient="linear(to-r, blue.500, cyan.500)">
      Continue with Google
    </GradientButton>
  );
}

export default GoogleLoginButton;
