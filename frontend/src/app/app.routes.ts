import { inject } from '@angular/core';
import { CanActivateFn, Router, Routes } from '@angular/router';
import { AuthService } from './core/auth.service';

/**
 * Sends anonymous visitors to the login form and remembers where they were
 * going, so submitting code or opening settings works after logging in.
 */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? true : router.createUrlTree(['/login'], { queryParams: { next: state.url } });
};

/** Keeps a logged-in visitor away from the login and register forms. */
export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? router.createUrlTree(['/problems']) : true;
};

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'problems' },
  {
    path: 'problems',
    title: 'Problems · CP Judge',
    loadComponent: () => import('./features/problems/problem-list').then((m) => m.ProblemList),
  },
  {
    path: 'problems/:slug',
    title: 'Problem · CP Judge',
    loadComponent: () =>
      import('./features/problems/problem-detail').then((m) => m.ProblemDetailPage),
  },
  {
    path: 'login',
    title: 'Log in · CP Judge',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login').then((m) => m.LoginPage),
  },
  {
    path: 'register',
    title: 'Register · CP Judge',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/register').then((m) => m.RegisterPage),
  },
  {
    path: 'submissions',
    title: 'My submissions · CP Judge',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/submissions/my-submissions').then((m) => m.MySubmissionsPage),
  },
  {
    path: 'submissions/:id',
    title: 'Submission · CP Judge',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/submissions/submission-detail').then((m) => m.SubmissionDetailPage),
  },
  {
    path: 'settings',
    title: 'Settings · CP Judge',
    canActivate: [authGuard],
    loadComponent: () => import('./features/settings/settings').then((m) => m.SettingsPage),
  },
  {
    path: '**',
    title: 'Page not found · CP Judge',
    loadComponent: () => import('./features/not-found').then((m) => m.NotFoundPage),
  },
];